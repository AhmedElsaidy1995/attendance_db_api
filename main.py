from flask import Flask, jsonify, request
import controller


app = Flask(__name__)


@app.route("/attendance/<employee>/<day>", methods=["GET"])
def get_attendance(employee=None, day=None):
    #employee = request.args.get('emp',None)
    #day = request.args.get('day',None)
    attendance = controller.check_attendance(employee,day)
    return jsonify(attendance)

@app.route("/record/<employee>", methods=["GET"])
def get_records(employee=None):
    record = controller.check_record(employee)
    return jsonify(record)

if __name__ == "__main__":

    app.run(host='0.0.0.0', port=8000, debug=False)
