from flask import Flask, render_template, request, session, jsonify, redirect
from database import UserDatabase
from otp_verification import OtpHandler
from youtube import third
from datetime import datetime, timezone

app = Flask(__name__)

app.secret_key = "super secret key"

db_manager = UserDatabase()
otp_manager = OtpHandler()

app.register_blueprint(third)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/decide')
def decide():
    if 'user_id' in session:
        return render_template('decide.html')
    else:
        return redirect('/login')
   

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/sentiment_analyzer')
def sentiment_analyzer():
    return render_template('sentiment_analyzer.html')

@app.route('/login_validation', methods=['POST'])
def login_validation():
    email = request.form.get('email')
    print("email: ",email)
    password = request.form.get('password')  
    print("password: ",password)

    try:
        user = db_manager.fetch_user_details(email,password) 
        print("user: ",user)
    except Exception as error:
        print("An Error occured while executing the query:", error)
        error = 'An Error Occured while trying to login. Please Try Again Later.'
        return render_template('login.html', error=error)
    
    if user:
        session['user_id'] = user.id
        session['name'] = user.name 

        return redirect('/decide') 
    else:
        error = 'Invalid Email id or Password'
        return render_template('login.html', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = {
            'name': request.form['name'],
            'email': request.form['email'],
            'password': request.form['password']
        }

        user_exists  = db_manager.check_user_exists(data['email'])

        if user_exists:
            error = 'A user with that email already exists.'
            return render_template('register.html', error=error)
        
        otp = otp_manager.generate_otp()
        session['otp'] = otp
        session['name'] = data['name']  
        session['password'] = data['password']  

        subject = 'OTP Verification'
        body = f'Your OTP for registration is: {otp}'
        to_email = data['email']

        if otp_manager.send_email(subject, body, to_email):
            session['email'] = data['email']
            return render_template('otp_verification.html', email=data['email'])
        else:
            return jsonify({"error": "Failed to send OTP via email."}), 500

    else:
        return render_template('register.html')

@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    data = request.form
    user_otp = data.get('otp')

    saved_otp = session.get('otp')
    email = session.get('email')
    name = session.get('name') 
    password = session.get('password') 


    print(f"user_otp: {user_otp}")
    print(f"saved_otp: {saved_otp}")
    print(f"email: {email}")

    if saved_otp and user_otp == saved_otp:
        data = {
            'name': name,
            'email': email,
            'password': password
        }
        db_manager.add_users_to_db(data)

        user_id_row = db_manager.check_user_exists(email)

        if user_id_row:
            user_id = user_id_row.id  
            session['user_id'] = user_id
        else:
            pass
        
        session['email'] = email
        session.pop('otp', None)
        session['name'] = name 
        session.pop('password', None)  

        return redirect('/decide')
    else:
        error = "Invalid OTP" 
        return render_template('otp_verification.html',error=error)

@app.route('/request_new_otp', methods=['GET'])
def request_new_otp():
    last_request_time = session.get('last_request_time')
    if last_request_time:
        last_request_time = last_request_time.replace(tzinfo=timezone.utc)

    current_time = datetime.utcnow().replace(tzinfo=timezone.utc)

    if last_request_time and (current_time - last_request_time).seconds < 60:
        return jsonify({"error": "You can request a new OTP after 60 seconds."}), 400

    session['last_request_time'] = current_time
    email = session.get('email')

    if email:
        new_otp = otp_manager.generate_otp()
        otp_manager.send_email('New OTP Request', f'Your new OTP for account registration is: {new_otp}\nPlease use this OTP to complete the registration process.', email)

        session['otp'] = new_otp
        current_time = datetime.utcnow()

    return render_template('otp_verification.html')

@app.route('/logout')
def logout():
    if 'user_id' in session:
        session.pop('user_id')
        return redirect('/login')
    else:
        return "user id not exist"

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)