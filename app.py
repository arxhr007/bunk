from flask import Flask, render_template, request, redirect, url_for, flash, session as flask_session, jsonify
import requests
import json
import os , random
app = Flask(__name__)
app.secret_key = "APP_KEY"
LOGIN_URL = "https://sahrdaya.etlab.in/user/login"
LOGOUT_URL = "https://sahrdaya.etlab.in/user/logout"
REFERRER = "https://sahrdaya.etlab.in/ktuacademics/student/viewattendancesubjectdutyleave/16"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/x-www-form-urlencoded"
}
PAYLOAD = {"format": "csv"}
try:
    with open("courses.json", "r") as json_file:
        sub = json.load(json_file)
except FileNotFoundError:
    sub = {}
@app.route('/')
def home():
    flask_session.clear()
    image_folder = 'static/vazhakal'  
    images = [f for f in os.listdir(image_folder) if f.endswith('.png')]
    random_image = random.choice(images) if images else None
    return render_template('login.html', logo=random_image, images=images)
@app.route('/get_random_logo')
def get_random_logo():
    image_folder = 'static/vazhakal'
    images = [f for f in os.listdir(image_folder) if f.endswith('.png')]
    if images:
        random_image = random.choice(images)
        return jsonify({"logo": url_for('static', filename=f'vazhakal/{random_image}')})
    return jsonify({"error": "No vazhakal found"}), 404
@app.route('/login', methods=['POST'])
def login():
    flask_session.clear()
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        flash('Username and password are required.', 'danger')
        return reload_login_page()
    with requests.Session() as session:
        login_payload = {
            "LoginForm[username]": username,
            "LoginForm[password]": password,
            "yt0": ""
        }
        try:
            login_response = session.post(LOGIN_URL, headers=HEADERS, data=login_payload, timeout=10)
            login_response.raise_for_status()
        except requests.RequestException as e:
            flash(f'Error logging in: {e}', 'danger')
            return reload_login_page()
        if "Invalid" in login_response.text:
            flash('Invalid username or password. ntha mone password marana?🤨.', 'danger')
            return reload_login_page()
        flask_session['session_cookies'] = json.dumps(session.cookies.get_dict())
        return redirect(url_for('display'))
def reload_login_page():
    image_folder = 'static/vazhakal'
    images = [f for f in os.listdir(image_folder) if f.endswith('.png')]
    random_image = random.choice(images) if images else None
    return render_template('login.html', logo=random_image, images=images)
@app.route('/get_attendance')
def get_attendance():
    if 'session_cookies' not in flask_session:
        return jsonify({"error": "Unauthorized access"}), 403
    cookies = json.loads(flask_session['session_cookies'])
    with requests.Session() as session_instance:
        session_instance.cookies.update(cookies)
        try:
            response = session_instance.post(REFERRER, headers=HEADERS, data=PAYLOAD, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            return jsonify({"error": f"Error fetching data: {e}"}), 500
        lines = response.text.splitlines()
        header = lines[1].replace('"', '').split(',')
        data = lines[2].replace('"', '').split(',')
        details_dict = dict(zip(header, data))
        session_instance.get(LOGOUT_URL, headers=HEADERS)
    name = details_dict.get("Name", "Unknown")
    Uni_Reg_No = details_dict.get("Uni Reg No", "N/A")
    Roll_no = details_dict.get("Roll No", "N/A")
    attendance_data = []
    for subject, attendance in details_dict.items():
        subject_name = sub.get(subject, subject)
        if subject_name.startswith("24"):
            subject_name = subject_name[2:]
        if '/' in attendance:
            attended, total = map(int, attendance.split(' ')[0].split('/'))
            attendance_data.append({
                "subject": subject_name,
                "attended": attended,
                "total": total
            })
    return jsonify({
        "name": name,
        "Uni_Reg_No": Uni_Reg_No,
        "Roll_no": Roll_no,
        "attendance_data": attendance_data
    })
@app.route('/display')
def display():
    return render_template('display.html')
if __name__ == '__main__':
    app.run(debug=True)