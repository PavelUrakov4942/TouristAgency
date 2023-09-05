import os
from dotenv import load_dotenv, find_dotenv
from flask import Flask, render_template, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
load_dotenv(find_dotenv())
app.secret_key = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DB_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
login_manager = LoginManager(app)
db = SQLAlchemy(app)


class User(db.Model, UserMixin):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=True)
    dob = db.Column(db.Date, nullable=True)
    phone = db.Column(db.String(11), nullable=True)
    email = db.Column(db.String(50), nullable=True, unique=True)
    hash_password = db.Column(db.String(500), nullable=True)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


class Contract(db.Model):
    __tablename__ = "contract"
    id_contract = db.Column(db.Integer, primary_key=True)
    series_number_passport = db.Column(db.String(20))
    address = db.Column(db.String(100))
    payment_type = db.Column(db.String(30))
    id_user = db.Column(db.Integer, db.ForeignKey("user.id"))
    id_group = db.Column(db.Integer, db.ForeignKey("tourist_group.id_group"))


# Маршрут
class Route(db.Model):
    __tablename__ = "route"
    id_route = db.Column(db.Integer, primary_key=True)
    price = db.Column(db.Numeric, nullable=True)
    insurance_sum = db.Column(db.Numeric, nullable=True)
    max_number_tourists = db.Column(db.Integer, nullable=True)
    min_number_tourists = db.Column(db.Integer, nullable=True)


# Группа
class Tourist_group(db.Model):
    __tablename__ = "tourist_group"
    id_group = db.Column(db.Integer, primary_key=True)
    number_tourists_in_group = db.Column(db.Integer, nullable=True)
    date_start = db.Column(db.Date, nullable=True)
    date_finish = db.Column(db.Date, nullable=True)
    id_route = db.Column(db.Integer, db.ForeignKey("route.id_route"))


# Путёвка
class Voucher(db.Model):
    __tablename__ = "voucher"
    id_voucher = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=True)
    dob = db.Column(db.Date)
    series_number_passport = db.Column(db.String(20))
    id_contract = db.Column(db.Integer, db.ForeignKey("contract.id_contract"))
    id_group = db.Column(db.Integer, db.ForeignKey("tourist_group.id_group"))


# Страна
class Country(db.Model):
    __tablename__ = "country"
    id_country = db.Column(db.Integer, primary_key=True)
    country_name = db.Column(db.String(20))


# Город
class City(db.Model):
    __tablename__ = "city"
    city_name = db.Column(db.String(20), primary_key=True)
    id_country = db.Column(db.Integer, db.ForeignKey("country.id_country"))


# Место прибытия
class Arrival_point(db.Model):
    __tablename__ = "arrival_point"
    id_arrival_point = db.Column(db.Integer, primary_key=True)
    number_days = db.Column(db.Integer)
    index_number = db.Column(db.Integer)
    id_route = db.Column(db.Integer, db.ForeignKey("route.id_route"))
    city_name = db.Column(db.String(20), db.ForeignKey("city.city_name"))


# Экскурсия
class Excursion(db.Model):
    __tablename__ = "excursion"
    id_excursion = db.Column(db.Integer, primary_key=True)
    excursion_name = db.Column(db.String(30))
    city_name = db.Column(db.String(20), db.ForeignKey("city.city_name"))


# Класс отеля
class Hotel_class(db.Model):
    __tablename__ = "hotel_class"
    id_class = db.Column(db.Integer, primary_key=True)
    class_name = db.Column(db.String(20))


# Отель
class Hotel(db.Model):
    __tablename__ = "hotel"
    id_hotel = db.Column(db.Integer, primary_key=True)
    hotel_name = db.Column(db.String(20))
    address = db.Column(db.String(100))
    city = db.Column(db.String(20), db.ForeignKey("city.city_name"))
    id_class = db.Column(db.Integer, db.ForeignKey("hotel_class.id_class"))


# Главная страница
@app.route("/")
def index():
    return render_template("index.html")


# Страница контактов
@app.route("/contacts")
def contacts():
    return render_template("contacts.html")


# Страница входа
@app.route("/login", methods=("POST", "GET"))
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.hash_password, password):
            login_user(user)
            next_page = request.args.get("next")
            return redirect(next_page)
        else:
            flash("Неверный логин или пароль.")

    return render_template("login.html")


# Обработчик выхода
@app.route("/logout", methods=("GET", "POST"))
@login_required
def logout():
    logout_user()
    return redirect("/")


# Страница регистрации
@app.route("/registration", methods=("POST", "GET"))
def registration():
    if request.method == "POST":
        try:
            hash = generate_password_hash(request.form["password"])
            user = User(
                full_name=request.form["fullname"],
                dob=request.form["dob"],
                phone=request.form["phone"],
                email=request.form["email"],
                hash_password=hash)
            db.session.add(user)
            db.session.commit()
            return redirect("/profile")
        except:
            db.session.rollback()
            flash(
                "Возникла ошибка при добавлении записи в базу данных. Проверьте корректность введённых данных. Возможно, пользователь с таким Email уже зарегистрирован.")

    return render_template("registration.html")


# Страница профиля
@app.route("/profile")
@login_required
def profile():
    user = User.query.get(current_user.id)
    history = Contract.query.order_by(Contract.id_contract.desc()).all()
    history_voucher = db.session.query(Voucher, Tourist_group, Route) \
        .join(Tourist_group, Voucher.id_group == Tourist_group.id_group) \
        .join(Route, Tourist_group.id_route == Route.id_route).all()
    return render_template("profile.html", user=user, history=history, history_voucher=history_voucher)


# Страница каталога
@app.route("/catalog")
def catalog():
    route = Route.query.all()
    tour = Tourist_group.query.all()
    return render_template("catalog.html", route=route, tour=tour)


# Страница тура
@app.route("/tour/<int:id_route>")
def tour(id_route):
    route_info = Route.query.get(id_route)
    group_info = Tourist_group.query.order_by(Tourist_group.id_group).all()
    route_list = db.session.query(Route, Arrival_point, City, Country, Excursion, Hotel, Hotel_class) \
        .join(Arrival_point, Route.id_route == Arrival_point.id_route) \
        .join(City, Arrival_point.city_name == City.city_name) \
        .join(Country, City.id_country == Country.id_country) \
        .join(Excursion, City.city_name == Excursion.city_name) \
        .join(Hotel, City.city_name == Hotel.city) \
        .join(Hotel_class, Hotel.id_class == Hotel_class.id_class).all()
    return render_template("tour.html", route_info=route_info, group_info=group_info, route_list=route_list)


# Страница ввода данных для договора
@app.route("/contract/group/<int:id_group>", methods=("POST", "GET"))
@login_required
def contract(id_group):
    if request.method == "POST":
        try:
            contract = Contract(
                id_user=current_user.id,
                id_group=id_group,
                series_number_passport=request.form["series_number_passport"],
                address=request.form["address"],
                payment_type=request.form["payment_type"]
            )
            db.session.add(contract)
            db.session.commit()
            return redirect("/final_contract")
        except:
            db.session.rollback()
            flash("Возникла ошибка при добавлении записи в базу данных. Проверьте корректность введённых данных.")
    return render_template("contract.html")


# Страница просмотра информации договора
@app.route("/final_contract", methods=("POST", "GET"))
@login_required
def final_contract():
    contract_info = db.session.query(User, Contract, Tourist_group) \
        .join(Contract, User.id == Contract.id_user) \
        .join(Tourist_group, Contract.id_group == Tourist_group.id_group) \
        .order_by(Contract.id_contract.desc()).first()
    return render_template("final_contract.html", contract_info=contract_info)


# Страница приобретения путёвок
@app.route("/voucher/<int:id_contract>/<int:id_group>", methods=("POST", "GET"))
@login_required
def voucher(id_contract, id_group):
    if request.method == "POST":
        try:
            voucher = Voucher(
                id_contract=id_contract,
                id_group=id_group,
                full_name=request.form["fullname"],
                dob=request.form["dob"],
                series_number_passport=request.form["series_number_passport"]
            )
            tourist_group = Tourist_group.query.get(id_group)
            tourist_group.number_tourists_in_group = tourist_group.number_tourists_in_group + 1
            db.session.add(voucher)
            db.session.commit()
            flash("Путёвка успешно добавлена к вашему договору.", category='success')
        except:
            db.session.rollback()
            flash("Возникла ошибка при добавлении записи в базу данных. Проверьте корректность введённых данных.",
                  category='error')
    return render_template("voucher.html")


# Страница просмотра всех купленных путёвок по договору
@app.route("/voucher_list", methods=("POST", "GET"))
@login_required
def voucher_list():
    buy = db.session.query(User, Contract, Tourist_group, Route) \
        .join(Contract, User.id == Contract.id_user) \
        .join(Tourist_group, Contract.id_group == Tourist_group.id_group) \
        .join(Route, Tourist_group.id_route == Route.id_route) \
        .order_by(Contract.id_contract.desc()).first()
    list = Voucher.query.all()
    return render_template("voucher_list.html", buy=buy, list=list)


# Обработчик удаления путёвки из договора
@app.route("/voucher_list_del_vouch/<int:id_voucher>", methods=("POST", "GET"))
@login_required
def voucher_list_del_vouch(id_voucher):
    voucher = Voucher.query.get(id_voucher)
    try:
        db.session.delete(voucher)
        tourist_group = Tourist_group.query.get(voucher.id_group)
        tourist_group.number_tourists_in_group = tourist_group.number_tourists_in_group - 1
        db.session.commit()
        flash("Путёвка успешно удалена.", category='success')
        return redirect("/voucher_list")
    except:
        db.session.rollback()
        flash("Возникла ошибка при удалении записи.", category='error')


# Перенаправление для гостя
@app.after_request
def redirect_to_signin(response):
    if response.status_code == 401:
        return redirect(("/login") + "?next=" + request.url)
    return response


if __name__ == "__main__":
    app.run()
