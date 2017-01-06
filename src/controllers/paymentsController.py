from flask import Blueprint, request
from src.common import Utils
from src.common.Respond import Respond
from src.models.User import User
from instamojo_wrapper import Instamojo
from src.models.Payment import Payment

payments_controller = Blueprint('payments', __name__)

API_KEY="3271e53813323e8876658e9ae76813c4"
AUTH_TOKEN="458cb9ae03afcfb91ad57f73db0796f2"

api = Instamojo(api_key=API_KEY, auth_token=AUTH_TOKEN)

packs = [
	{
		"id": 1,
		"points": 50,
		"cost": 10
	},
	{
		"id": 2,
		"points": 200,
		"cost": 20
	},
	{
		"id": 3,
		"points": 500,
		"cost": 50
	}
]

@payments_controller.route('/pack/<int:pack_id>')
@Utils.auth_required
def pay_for_pack(user, pack_id):

	for pack in packs:
		if pack['id'] == pack_id:
			selected_pack = pack
			break;
	else:
		return Respond.error("Pack not valid", error_code=402)    	

	payment_request = Payment(
		user=user.key,
		cost=selected_pack['cost'],
		points=selected_pack['points']
	)

	payment_request.put()

	response = api.payment_request_create(
	    amount=payment_request.cost,
	    purpose="test",
	    email=user.email,
	    webhook="https://3-dot-noted-api.appspot.com/study/payments/webhook"
	    )

	print response

	payment_request.request_url = response['payment_request']['longurl']
	payment_request.request_id = response['payment_request']['id']

	payment_request.put()


	return Respond.success({ "url": payment_request.request_url })

