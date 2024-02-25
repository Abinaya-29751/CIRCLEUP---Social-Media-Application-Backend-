from flask import Flask, jsonify, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, current_user, UserMixin, logout_user
import mysql.connector
import os
from werkzeug.utils import secure_filename
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to your secret key

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

# Connect to MySQL database
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="abinaya29",  # Update with your MySQL password
    database="socialMedia"
)
cursor = db.cursor()

# Create users table if not exists
cursor.execute('''CREATE TABLE IF NOT EXISTS users
             (id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(100) UNIQUE, password VARCHAR(100), email VARCHAR(100))''')
db.commit()

# Define User model for Flask-Login
class User(UserMixin): 
    def __init__(self, user_id):
        self.id = user_id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        cursor.execute("INSERT INTO users (username, password, email) VALUES (%s, %s, %s)", (username, password, email))
        db.commit()
        
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()
        
        if user:
            user_id = user[0]
            user_obj = User(user_id)
            login_user(user_obj)
            return redirect(url_for('home', user_id=user_id))
        else:
            flash('Invalid username or password', 'error')
            return redirect(url_for('index'))

@app.route('/home/<int:user_id>')
@login_required
def home(user_id):
    cursor.execute("SELECT posts.content, users.username FROM posts INNER JOIN users ON posts.user_id = users.id")
    all_posts = cursor.fetchall()
    
    return render_template('home.html', user_posts=all_posts, user_id=user_id)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))
UPLOAD_FOLDER = 'uploads'  # Directory where uploaded images will be saved
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}  # Allowed image file extensions

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image(image_file):
    if image_file and allowed_file(image_file.filename):
        filename = secure_filename(image_file.filename)
        image_path = os.path.join(UPLOAD_FOLDER, filename)
        image_file.save(image_path)
        return image_path
    else:
        raise ValueError('Invalid or unsupported file format')
@app.route('/add_post', methods=['POST'])
def add_post():
    user_id = request.form['user_id']
    caption = request.form['post']
    image_file = request.files['image']
    
    # Assuming you have a function to save the image file and get its path
    image_path = save_image(image_file)  # Define 'image_path' after saving the image

    # Insert the post into the database
    cursor.execute("INSERT INTO posts (user_id, content, image_path) VALUES (%s, %s, %s)", (user_id, caption, image_path))
    db.commit()

    # Redirect to the home page after adding the post
    return redirect(url_for('home', user_id=user_id))



@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        new_username = request.form['new_username']
        new_password = request.form['new_password']
        
        cursor.execute("UPDATE users SET username = %s, password = %s WHERE id = %s", (new_username, new_password,  current_user.id))
        db.commit()

        return jsonify({'message': 'Profile updated successfully'})

    cursor.execute("SELECT username, email FROM users WHERE id = %s", (current_user.id,))
    user_details = cursor.fetchone()
    user_details_dict = {
        'username': user_details[0],
        'email': user_details[1],
    }
    return render_template('profile.html', user_details=user_details_dict)

def query_users_by_username(username):
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    users = cursor.fetchall()
    return users

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        search_query = request.form.get('search_query')
        users = query_users_by_username(search_query)
        if users:
            user = users[0]
            user_id = user[0]
            
            cursor.execute("SELECT content FROM posts WHERE user_id = %s", (user_id,))
            user_posts = cursor.fetchall()
            
            return render_template('user_profile.html', user=user, user_posts=user_posts)
        else:
            flash('User not found', 'error')
            return redirect(url_for('home'))
    else:
        return render_template('search_form.html')

if __name__ == '__main__':
    app.run(debug=True)
