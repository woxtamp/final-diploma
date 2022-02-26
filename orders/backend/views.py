from django.contrib.auth import authenticate

from django.db.models import Q

from django.contrib.auth.password_validation import validate_password

from django.http import JsonResponse

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet

from rest_framework.authtoken.models import Token

import yaml

from backend.models import Category, Shop, ProductInfo, Product, Parameter, ProductParameter, Order, OrderItem, Contact
from backend.serializer import CategorySerializer, ShopSerializer, UserSerializer, ProductInfoSerializer, \
    OrderSerializer, OrderItemSerializer, ContactSerializer, ContactSerializerCreate


class PartnerPriceLoad(APIView):
    # загрузка данных от поставщика
    def post(self, request, *args, **kwargs):

        if not request.user.is_authenticated:
            return JsonResponse({'Status': False,
                                 'Error': 'Access denied! Available only for registered users.'},
                                status=403)

        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Access denied! Available only for shops.'},
                                status=403)

        file = request.data.get('url')

        if file:
            data = yaml.load(file, Loader=yaml.FullLoader)
            shop, _ = Shop.objects.get_or_create(name=data['shop'], user_id=request.user.id)

            for category in data['categories']:
                category_object, _ = Category.objects.get_or_create(id=category['id'], name=category['name'])
                category_object.shops.add(shop.id)
                category_object.save()

            ProductInfo.objects.filter(shop_id=shop.id).delete()
            for item in data['goods']:
                product, _ = Product.objects.get_or_create(name=item['name'], category_id=item['category'])

                product_info = ProductInfo.objects.create(product_id=product.id,
                                                          external_id=item['id'],
                                                          model=item['model'],
                                                          price=item['price'],
                                                          price_rrc=item['price_rrc'],
                                                          quantity=item['quantity'],
                                                          shop_id=shop.id)
                for name, value in item['parameters'].items():
                    parameter_object, _ = Parameter.objects.get_or_create(name=name)
                    ProductParameter.objects.create(product_info_id=product_info.id,
                                                    parameter_id=parameter_object.id,
                                                    value=value)

            return JsonResponse({'Status': True})

        return JsonResponse({'Status': False, 'Errors': 'Input Error! All required fields are not filled.'})


class CategoryView(ReadOnlyModelViewSet):
    # просмотр категорий
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    search_fields = ["name"]


class ShopView(ReadOnlyModelViewSet):
    # просмотр магазинов
    queryset = Shop.objects.filter(state=True)
    serializer_class = ShopSerializer

    search_fields = ['name']


class ProductInfoView(ReadOnlyModelViewSet):
    # просмотр продуктов
    serializer_class = ProductInfoSerializer

    search_fields = ['product__name', 'model']

    def get_queryset(self):
        query = Q(shop__state=True)

        shop_id = self.request.GET.get('shop_id', None)
        category_id = self.request.GET.get('category_id', None)

        if shop_id:
            query = query & Q(shop_id=shop_id)

        if category_id:
            query = query & Q(product__category_id=category_id)

        queryset = ProductInfo.objects.filter(query).select_related(
            'shop', 'product__category').prefetch_related(
            'product_parameters__parameter').distinct()

        return queryset


class UserLogin(APIView):
    # получение токена
    def post(self, request,):

        if {'email', 'password'}.issubset(request.data):
            user = authenticate(request, username=request.data['email'], password=request.data['password'])

            if user is not None:
                if user.is_active:
                    token, created = Token.objects.get_or_create(user=user)

                    return JsonResponse({'Status': True, 'Token': token.key})

            return JsonResponse({'Status': False, 'Errors': 'Authorisation Error.'})

        return JsonResponse({'Status': False, 'Errors': 'Input Error! All required fields are not filled.'})


class UserRegister(APIView):
    # регистрация покупателя
    def post(self, request, *args, **kwargs):
        if {'first_name', 'last_name', 'email', 'password', 'company', 'position'}.issubset(request.data):
            try:
                validate_password(request.data['password'])
            except Exception as password_error:
                list_error = []
                for item in password_error:
                    list_error.append(item)
                return JsonResponse({'Status': False, 'Errors': {'password': list_error}})
            else:
                user_serializer = UserSerializer(data=request.data)
                if user_serializer.is_valid():
                    user = user_serializer.save()
                    user.set_password(request.data['password'])
                    user.save()
                    return JsonResponse({'Status': True})
                else:
                    return JsonResponse({'Status': False, 'Errors': user_serializer.errors})

        return JsonResponse({'Status': False, 'Errors': 'Input Error! All required fields are not filled.'})


class PartnerOrdersView(APIView):
    # просмотр заказа поставщиком
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False,
                                 'Error': 'Access denied! Available only for registered users.'},
                                status=403)

        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Access denied! Available only for shops.'},
                                status=403)

        order = Order.objects.filter(
            ordered_items__product_info__shop__user_id=request.user.id).exclude(state='basket').prefetch_related(
            'ordered_items__product_info__product__category')

        serializer = OrderSerializer(order, many=True)
        return Response(serializer.data)


class BasketView(APIView):
    # действия с корзиной покупателя
    def get(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False,
                                 'Error': 'Input Error! All required fields are not filled.'},
                                status=403)
        basket = Order.objects.filter(
            user_id=request.user.id, state='basket').prefetch_related(
            'ordered_items__product_info__product__category')

        serializer = OrderSerializer(basket, many=True)
        return Response(serializer.data)

    def post(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False,
                                 'Error': 'Input Error! All required fields are not filled.'},
                                status=403)

        items = request.data.get('ordered_items')

        if items:
            basket, created = Order.objects.get_or_create(user_id=request.user.id, state='basket')

            objects_created = 0
            for item in items:

                exists_item = OrderItem.objects.filter(order=basket.id, product_info=item["product_info"])
                if len(exists_item) > 0:
                    return JsonResponse({'Status': False, 'Errors': f'Position {item["product_info"]} '
                                                                    f' already added.'})

                item.update({'order': basket.id})
                serializer = OrderItemSerializer(data=item)
                if serializer.is_valid():
                    serializer.save()
                    objects_created += 1
                else:
                    return JsonResponse({'Status': False, 'Errors': serializer.errors})

            return JsonResponse({'Status': True, 'Positions created:': objects_created})

        return JsonResponse({'Status': False, 'Errors': 'Input Error! All required fields are not filled.'})

    # удалить позиции из корзины
    def delete(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False,
                                 'Error': 'Access denied! Available only for registered users.'},
                                status=403)

        items = request.data.get('ordered_items')

        if items:
            basket, created = Order.objects.get_or_create(user_id=request.user.id, state='basket')

            query = Q()
            for item in items:
                query = query | Q(order_id=basket.id, product_info=item["product_info"])

            deleted_count = OrderItem.objects.filter(query).delete()[0]

            return JsonResponse({'Status': True, 'Positions deleted': deleted_count})

        return JsonResponse({'Status': False, 'Errors': 'Input Error! All required fields are not filled.'})

    def put(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False,
                                 'Error': 'Access denied! Available only for registered users.'},
                                status=403)

        items = request.data.get('ordered_items')

        if items:
            basket, created = Order.objects.get_or_create(user_id=request.user.id, state='basket')

            objects_updated = 0
            for item in items:
                objects_updated += OrderItem.objects.filter(order_id=basket.id, product_info=item['product_info']).\
                    update(quantity=item['quantity'])

                return JsonResponse({'Status': True, 'Objects updated': objects_updated})

        return JsonResponse({'Status': False, 'Errors': 'Input Error! All required fields are not filled.'})


class ContactView(APIView):
    def get(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False,
                                 'Error': 'Access denied! Available only for registered users.'},
                                status=403)
        contact = Contact.objects.filter(user_id=request.user.id)
        serializer = ContactSerializer(contact, many=True)
        return Response(serializer.data)

    def post(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False,
                                 'Error': 'Access denied! Available only for registered users.'},
                                status=403)

        if {'city', 'street', 'house', 'phone'}.issubset(request.data):
            request.data.update({'user': request.user.id})
            serializer = ContactSerializerCreate(data=request.data)

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=201)
            else:
                return JsonResponse({'Status': False, 'Errors': serializer.errors})

        return JsonResponse({'Status': False, 'Errors': 'Input Error! All required fields are not filled.'})

    def put(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False,
                                 'Error': 'Access denied! Available only for registered users.'},
                                status=403)

        if 'id' in request.data:
            if request.data['id'].isdigit():
                contact = Contact.objects.filter(id=request.data['id'], user_id=request.user.id).first()

                if contact:
                    request.data.update({'user': request.user.id})
                    serializer = ContactSerializer(contact, data=request.data, partial=True)

                    if serializer.is_valid():
                        serializer.save()
                        return Response(serializer.data)
                    else:
                        return JsonResponse({'Status': False, 'Errors': serializer.errors})

        return JsonResponse({'Status': False, 'Errors': 'Input Error! All required fields are not filled.'})

    def delete(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False,
                                 'Error': 'Access denied! Available only for registered users.'},
                                status=403)

        contact_id = request.data.get('id')

        if contact_id:
            if contact_id.isdigit():
                Contact.objects.filter(Q(user_id=request.user.id, id=contact_id)).delete()
                return JsonResponse({'Status': True})

        return JsonResponse({'Status': False, 'Errors': 'Input Error! All required fields are not filled.'})


class OrderView(APIView):
    # действия с заказами покупателем
    def get(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False,
                                 'Error': 'Access denied! Available only for registered users.'},
                                status=403)

        order = Order.objects.filter(
            user_id=request.user.id).exclude(state='basket').prefetch_related(
            'ordered_items__product_info__product__category',
            'ordered_items__product_info__product_parameters__parameter').select_related('contact').distinct()

        serializer = OrderSerializer(order, many=True)

        return Response(serializer.data)

    def post(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False,
                                 'Error': 'Access denied! Available only for registered users.'},
                                status=403)

        id_order = request.data['id']

        if id_order:

            data = Order.objects.filter(id=id_order, user=request.user.id, state='basket')

            if len(data) == 0:
                return JsonResponse({'Status': False, 'Errors': 'Error! Shopping cart not found.'})

            data.update(state='new')

            return JsonResponse({'Status': True})

        return JsonResponse({'Status': False, 'Errors': 'Input Error! All required fields are not filled.'})
