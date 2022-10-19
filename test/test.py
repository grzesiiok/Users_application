import psycopg2
import redis
from fastapi.testclient import TestClient
import pytest
import main
from main import app
from main import engine
from sqlalchemy import insert
import random
import string
from sqlmodel import SQLModel, create_engine, Field, Session,select
import  aio_pika
import pika

client = TestClient(app)

class UserEntity():
    def __init__(self,ID=None, countryCode=None,dateofbirth=None, firstname=None,
                 lastname=None,nickname=None, gender=None, email=None):
        self.ID = ID
        self.countryCode = countryCode
        self.dateofbirth = dateofbirth
        self.firstName = firstname
        self.lastname = lastname
        self.nickname = nickname
        self.gender = gender
        self.email = email

    def validation(self):
        if type(self.ID) is int or self.ID is None or type(self.ID) is list:
            valid = True
        else: return False
        for i in [self.countryCode,self.dateofbirth,self.firstName,self.lastname,
                  self.nickname,self.gender,self.email]:
            if type(i) is str or i is None:
                valid = True
            else: return False
        return valid

    def generate_user(self):
        if self.validation() == True:
            return {"id": self.ID,
            "countryCode": self.countryCode,
            "dateOfBirth": self.dateofbirth,
            "firstName": self.firstName,
            "lastName": self.lastname,
            "nickname": self.nickname,
            "gender": self.gender,
            "email": self.email}
        else: print("invalid data type")

    def make_request(self):
        if self.validation() == True:
            req = "/v1/users"
            if self.ID is not None:
                if type(self.ID) == list:
                    req += "?"
                    for value in self.ID:
                        req = req + "ids=" + str(value) + "&"
                    if [self.email, self.nickname] is not None:
                        req = req[:-1]
                elif type(self.ID) != list:
                    req = req + "?ids=" + str(self.ID)
                    if [self.email, self.nickname] is not None: req = req + "&"
            if [self.email, self.nickname] is not None and self.ID is None: req = req + "?"
            for key, value in {"nickname": self.nickname, "email": self.email}.items():
                if value is not None:
                    req = req + str(key) + "=" + str(value) + "&"
            return str(req)
        else:
            print("invalid data type")

    def Id_link(self):
        if self.validation() == True:
            req = "/v1/users/" + str(self.ID)
            return req
        else:
            print("invalid data type")



def test_users():
    main.create_tables()
    with Session(engine) as session:
        usr1 = session.exec(select(main.User).where(main.User.id == 1)).first()
        usr2 = session.exec(select(main.User).where(main.User.id == 2)).first()
        usr3 = session.exec(select(main.User).where(main.User.id == 3)).first()
        if usr1:
            session.delete(usr1)
        session.add(main.User(id=1,
        countryCode="PL",
        dateOfBirth="21-11-2021",
        firstName="James",
        lastName="Wazowskyy",
        nickname="b_psychedelic",
        gender="male",
        email="will.be.psychedelic@gmail.com", )
        )
        if usr2:
            session.delete(usr2)
        session.add(main.User(id=2,
        countryCode="PL",
        dateOfBirth="19-11-2021",
        firstName="Jon",
        lastName="Kowal",
        nickname="mayb_hedel",
        gender="female",
        email="will.be.not.psychedelic@gmail.com", )
        )
        if usr3:
            session.delete(usr3)
        session.add(main.User(id=3,
        countryCode="PL",
        dateOfBirth="19-9-2021",
        firstName="Jones",
        lastName="Kowalskyy",
        nickname="mayb_psychedelic",
        gender="male",
        email="psychedelic@gmail.com", )
        )

        session.commit()
        session.close()
        return usr1,usr2,usr3

test_users()
usr1, usr2, usr3 = test_users()




def all_usr():
    with Session(engine) as session:
        users = session.exec(select(main.User)).all()
        return users





@pytest.mark.parametrize("path, exp_status_code, responses",[
    (UserEntity().make_request(), 200, all_usr()),
    (UserEntity(ID=1).make_request(), 200, [usr1.dict()]),
    # # (UserEntity(ID=[1,2]).make_request(), 200, [main.Userslist[0],main.Userslist[1]]),
    (UserEntity(nickname="b_psychedelic").make_request(), 200, [usr1.dict()]),
    (UserEntity(email="will.be.psychedelic%40gmail.com").make_request(), 200, [usr1.dict()]),
    (UserEntity(nickname="b_psychedelic",email="will.be.psychedelic%40gmail.com",).make_request(), 405, {"detail": "method not allowed"}),
    (UserEntity(ID=1,nickname="b_psychedelic",email="will.be.psychedelic%40gmail.com").make_request(), 405,{"detail": "method not allowed"}),
    ])

def test_search_and_filter(path,exp_status_code, responses):
    response = client.get(path)
    assert response.status_code == exp_status_code
    assert response.json() == responses



def test_add_new_user_with_existing_user():

    request_body1 = UserEntity(1,"UA","24-08-1991","James","Morrison","b_psychedelic","male","will.be.psychedelic@gmail.com").generate_user()
    response = client.post(UserEntity().make_request(), json=request_body1)
    assert response.status_code == 422
    assert response.json() == {"detail": "User exists"}

    request_body2 = UserEntity(1,"UA","24-08-1991","James","Morrison","psychedelic","male","will.be.psychedelic@gmail.com").generate_user()
    response = client.post(UserEntity().make_request(), json=request_body2)
    assert response.status_code == 422
    assert response.json() == {"detail": "User exists"}


    request_body3 = UserEntity(1,"UA","24-08-1991","James","Morrison","b_psychedelic","male","psychedelic@gmail.com").generate_user()
    response = client.post(UserEntity().make_request(), json=request_body3)
    assert response.status_code == 422
    assert response.json() == {"detail": "User exists"}

gen_id = random.randint(3,10000)
def test_add_new_user_with_new_user():
    letters = string.ascii_lowercase
    request_body = UserEntity(gen_id,"UA","24-08-1991","James","Morrison",''.join(random.choice(letters) for i in range(10)),"male",''.join(random.choice(letters) for i in range(10))).generate_user()


    response = client.post(UserEntity().make_request(), json=request_body)
    assert response.status_code == 200
    assert response.json() == request_body



@pytest.mark.parametrize("path, exp_status_code, responses",[
    (UserEntity(1).Id_link(), 200, [usr1]),
    (UserEntity(2).Id_link(), 200, [usr2]),
    (UserEntity(1300).Id_link(), 404, {'detail': 'Cannot find user'}),
    (UserEntity(1301).Id_link(), 404, {'detail': 'Cannot find user'}),
    ])
def test_searching_by_id(path,exp_status_code,responses):
    response = client.get(path)
    assert response.status_code == exp_status_code
    assert response.json() == responses


def test_update_user():
    request_body1 = UserEntity(1, "UA", "24-08-1991", "James", "Morrison", "b_psychedelico", "male","will.be.psychedelico@gmail.com").generate_user()
    del request_body1["id"]

    resp = {
      "countryCode": "UA",
      "dateOfBirth": "24-08-1991",
      "lastName": "Morrison",
      "gender": "male",
      "firstName": "James",
      "id": 1,
      "nickname": "b_psychedelico",
      "email": "will.be.psychedelico@gmail.com"
    }

    resp404 = {"detail": "User not found"}

    response = client.put(UserEntity(1).Id_link(), json=request_body1)
    assert response.status_code == 200
    assert response.json() == resp

    response = client.put(UserEntity(1200).Id_link(), json=request_body1)
    assert response.status_code == 404
    assert response.json() == resp404


@pytest.mark.parametrize("path, exp_status_code, responses",[
    (UserEntity(1).Id_link(), 200, {"message": "user 1 has been deleted"}),
    (UserEntity(2).Id_link(), 200, {"message": "user 2 has been deleted"}),
    (UserEntity(gen_id).Id_link(), 200, {"message": f"user {gen_id} has been deleted"}),
    (UserEntity(1400).Id_link(), 404, {'detail': 'Cannot find user'}),
    (UserEntity(1401).Id_link(), 404, {'detail': 'Cannot find user'}),
    ])
def test_deleting_by_id(path,exp_status_code, responses):
    response = client.delete(path)
    assert response.status_code == exp_status_code
    assert response.json() == responses


def test_db_connection():
    conn = psycopg2.connect(dbname= "postgres",user="postgres",host="postgres",password="password",port="5432")
    assert conn.closed == 0

import redis
def test_redis():
    redis_host = "redis://redis:6379"
    r = redis.from_url(redis_host)
    print(r.ping())


def test_rabbit():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbit'))
    channel = connection.channel()
    channel.queue_purge("status_queue")

