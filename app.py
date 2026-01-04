from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from flask_mail import Mail, Message
import os

app= Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'gym.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config ['SECRET_KEY']='mygymsecretkey'
db=SQLAlchemy(app)
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT']=587
app.config['MAIL_USE_TLS']=True
app.config['MAIL_USERNAME']='Your email addres'
app.config['MAIL_PASSWORD']='Your App mail passowrd'
app.config['MAIL_DEFAULT_SENDER']='Your email addres"

mail=Mail(app)

def generate_receipt(member):
     receipt_dir='receipts'
     os.makedirs(receipt_dir,exist_ok=True)
     file_path=f"{receipt_dir}/receipt_{member.id}.pdf"
     c=canvas.Canvas(file_path, pagesize=A4)
     width, height = A4
     c.setFont("Helvetica-Bold", 16)
     c.drawString(50, height - 50, "Gym Membership Receipt")
     c.setFont("Helvetica", 12)
     c.drawString(50,height-120,f"Member Name: {member.name}")
     c.drawString(50,height-150,f"Mobile Number: {member.mobile_number}")
     c.drawString(50,height-180,f"Email: {member.Email}")
     c.drawString(50,height-210,f"Fees Paid: ₹{member.Fees}")
     c.drawString(50,height-240,f"Joining Date: {member.joining_date}")
     c.drawString(50,height-270,f"End Date: {member.End_date}")
     c.drawString(50,height-300,f"Payment Mode: {member.payment_mode}")
     c.drawString(50,height-360,f"Thank you for choosing our gym!")
     c.showPage()
     c.save()
     return file_path
def send_receipt_email(member, file_path):
    msg = Message(
        subject="Gym Membership Receipt",
        recipients=[member.Email]
    )

    msg.body = f"""
Hello {member.name},

Thank you for joining us.

Please find attached your membership fee receipt.

Regards,
SpaceX Gym
"""

    with open(file_path, "rb") as f:
        msg.attach(
            filename="fee_receipt.pdf",
            content_type="application/pdf",
            data=f.read()
        )

    mail.send(msg)


class Members(db.Model):
     __tablename__='members'
     id=db.Column(db.Integer,primary_key=True)
     name=db.Column(db.String(200),nullable=False)
     mobile_number=db.Column(db.String(15),nullable=False)
     Email=db.Column(db.String(100),nullable=False)
     Fees=db.Column(db.Float,nullable=False)
     joining_date=db.Column(db.Date,default=lambda:datetime.utcnow().date())
     End_date=db.Column(db.Date,nullable=False)
     payment_mode=db.Column(db.String(50),nullable=False)
     status=db.Column(db.String(20),default='Active')
     
     
with app.app_context():
     db.create_all()

@app.route('/')
def index():
     if 'user_id' not in session:
          return redirect('/login')
     return render_template('index.html')
     
@app.route('/login', methods=['GET','POST'])
def login():
     if request.method == 'POST':
          username=request.form.get('username')
          password=request.form.get('password')
          if username == "owais" and password == "owais123":
               session['user_id'] = 1
               return redirect('/')
          else:
               return 'Invalid credentials'
     return render_template('login.html')
     
@app.route('/logout')
def logout():
     session.clear()
     return redirect('/login')
@app.route('/send-receipt')
def send_receipt():
     if 'user_id' not in session:
          return redirect('/login')
     return render_template('send-receipt.html')

@app.route('/add-member',methods=['GET','POST'])
def add_member():
     if 'user_id' not in session:
          return redirect('/login')
     if request.method == 'POST':
          name=request.form.get("member_name")
          mobile=request.form.get("mobile")
          email=request.form.get("email")
          fees=request.form.get("amount")
          start_date=request.form.get("start_date")
          end_date=request.form.get("end_date")
          payment_mode=request.form.get("payment_mode")
          joining_date=datetime.strptime(start_date,"%Y-%m-%d").date()
          end_date_d=datetime.strptime(end_date,"%Y-%m-%d").date()
          today_date=datetime.utcnow().date()
          
          if end_date_d < today_date:
               status='Inactive'
          else:
               status='Active'
               

          new_member=Members(
               name=name,
               mobile_number=mobile,
               Email=email,
               Fees=fees,
               joining_date=joining_date,
               End_date=end_date_d,
               payment_mode=payment_mode,
               status=status
          )
          db.session.add(new_member)
          db.session.commit()
          pdf_path=generate_receipt(new_member)
          send_receipt_email(new_member,pdf_path)
          return redirect('/')
     return render_template('send-receipt.html')
@app.route('/members',methods=['GET'])
def members():
     if 'user_id' not in session:
          return redirect('/login')
     members=Members.query.all()
     active_count=Members.query.filter_by(status='Active').count()
     return render_template(
          'member.html',
          members=members,
          active_count=active_count
     )
@app.route('/search',methods=['GET'])
def search():
     if 'user_id' not in session:
          return redirect('/login')
     query=request.args.get('search')
     members=[]
     if query:
          members=Members.query.filter(Members.name.ilike(f'%{query}%')).all()
     else:
          members=Members.query.all()
     active_count=Members.query.filter_by(status='Active').count()
     return render_template(
               'member.html',
               members=members,
               active_count=active_count,
               query=query
          )
@app.route('/delete-member/<int:id>', methods=['POST'])
def delete_member(id):
     if 'user_id' not in session:
          return redirect('/login')
     member=Members.query.get_or_404(id)
     db.session.delete(member)
     db.session.commit()
     return redirect('/members')

if __name__ == '__main__':
     app.run(debug=True)
