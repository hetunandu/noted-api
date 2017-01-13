from flask import Blueprint, request
from src.common import Utils
from src.common.Respond import Respond
from src.models.User import User
from src.models.Payment import Payment
import requests

payments_controller = Blueprint('payments', __name__)

API_KEY="3271e53813323e8876658e9ae76813c4"
AUTH_TOKEN="458cb9ae03afcfb91ad57f73db0796f2"

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

@payments_controller.route('/request')
@Utils.auth_required
def request_payment(user):

	payment_request = Payment(
		user=user.key,
		cost=50,
		points=500,
		status="Pending"
	)

	payment_request.put()

	headers = { "X-Api-Key": API_KEY, "X-Auth-Token": AUTH_TOKEN}
	payload = {
	  'purpose': "Noted coins",
	  'amount': payment_request.cost,
	  'buyer_name': user.name,
	  'email': user.email,
	  'webhook': 'https://noted-api.appspot.com/study/payments/webhook',
	  'allow_repeated_payments': 'False',
	}
	
	response = requests.post("https://www.instamojo.com/api/1.1/payment-requests/", data=payload, headers=headers)

	insta_request = response.json()

	if insta_request['success'] == False:
		return Respond.error(insta_request['message'])


	payment_request.request_url = insta_request['payment_request']['longurl']
	payment_request.request_id = insta_request['payment_request']['id']

	payment_request.put()

	return Respond.success({
		'payment_request': insta_request['payment_request'],
		'payment_key': payment_request.key.urlsafe()
		})


@payments_controller.route('/webhook', methods=['POST'])
def payment_webhook():
	post=request.form

	payment_request = Payment.query(Payment.request_id == post['payment_request_id']).get()

	payment_request.status = post['status']
	payment_request.payment_id = post['payment_id']

	payment_request.put()

	if payment_request.status == 'Credit':

		user = payment_request.user.get()

		user.addPoints(payment_request.points, 'Paid online {}'.format(payment_request.payment_id))


	return Respond.success('Thanks Instamojo')


@payments_controller.route('/status/<payment_key>')
@Utils.auth_required
def payment_status(user, payment_key):
	payment_request = Utils.urlsafe_to_key(payment_key).get()

	return Respond.success({'status': payment_request.status})





