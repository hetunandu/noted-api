from google.appengine.ext import ndb
from flask import Blueprint, request, send_file
from src.common import Utils
from src.common.Respond import Respond
from src.models.UserCodes import UserCodes
import string
import random
import StringIO
import xlsxwriter

codes_controller = Blueprint('codes', __name__)


@codes_controller.route('/')
@Utils.admin_required
def create(user):
	"""
	Create codes. Save in datastore and get excel file
	"""

	for i in range(1, 1000):
		code = code_generator(size=5)
		srno = i

		usercode = UserCodes(
			srno=i,
			code=code,
			points=500
			)

		usercode.put()

	return Respond.success('yo')


@codes_controller.route('/addrep', methods=['POST'])
@Utils.admin_required
def assign_rep(user):
	"""
	Assign rep to list of codes
	"""
	post = Utils.parse_json(request)

	codes = UserCodes.query(UserCodes.srno >= post['start'], UserCodes.srno <= post['end'])


	for code in codes:
		code.repName = post['repName']
		code.put()

	return Respond.success('yo')

# @codes_controller.route('/excel')
# def create_excel():
# 	# Create an in-memory output file for the new workbook.
#     output = StringIO.StringIO()

#     # Even though the final file will be in memory the module uses temp
#     # files during assembly for efficiency. To avoid this on servers that
#     # don't allow temp files, for example the Google APP Engine, set the
#     # 'in_memory' constructor option to True:
#     workbook = xlsxwriter.Workbook(output, {'in_memory': True})
#     worksheet = workbook.add_worksheet()

#     # Write some test data.
#     worksheet.write(0, 0, 'Sr No')
#     worksheet.write(0, 1, 'Code')

#     row = 1
#     col = 0

#     codes = UserCodes.query().order(UserCodes.srno)

#     for code in codes:
#     	worksheet.write(row, col, code.srno)
#     	worksheet.write(row, col + 1, code.code)
#     	row += 1


#     # Close the workbook before streaming the data.
#     workbook.close()

#     # Rewind the buffer.
#     output.seek(0)

#     return send_file(output)


def code_generator(size=6, chars=string.ascii_uppercase + string.digits):
	return ''.join(random.choice(chars) for _ in range(size))