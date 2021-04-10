from rest_framework.views import APIView
from rest_framework.response import Response


class PaymentJumpView(APIView):

    def post(self, request):
        order_id = request.data['order_id']
        amount = request.data['amount']

        return Response()
