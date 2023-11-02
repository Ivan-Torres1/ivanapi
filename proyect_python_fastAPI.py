from fastapi import FastAPI,Depends, HTTPException,status
from pydantic import BaseModel,EmailStr,constr
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt,JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
import pymysql





"""

{"name":"Marta",
"lastname":"Flores",
"password":"Familia123",
"email":"lamartamanda@gmail.com"}

# PatriManda123


"""

app = FastAPI()



# CONECTION DATA BASE

host = "bg28d8zi0klbkaf2ouaj-mysql.services.clever-cloud.com"
database = "bg28d8zi0klbkaf2ouaj"
useer = "uf1mtpwwj4mcgrfv"
password = "1ZoAJ8ocpceH1XcWFDII"




conn = pymysql.connect(host=host,port=3306,user=useer,db=database,passwd=password)
cursor = conn.cursor()


# VARIABLES
oauth2 = OAuth2PasswordBearer(tokenUrl="login")
ACCES_TOKEN_DURATION = 5
SECRET = "b8180510ef47b510a20a0410eca9cead13c81cf313f3a196453a78c0af02a429"
ALGORITHM = "HS256"
crypt = CryptContext(schemes=["bcrypt"])

#                                       Funciones 
def VerifyUser(email,name):
    cursor.execute("SELECT id FROM users WHERE email=%s or name=%s",[email,name])
    date = cursor.fetchall()
    if date:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                            detail="Su gmail o nombre de usuario ya se ha usado para crear una cuenta",
                            headers={"ERROR":"NOT ACCEPTABLE"})
    pass


def Haspassword(password):
    hasheo = crypt.hash(password)
    return hasheo






#                           basemodel

class User(BaseModel):
    name: constr(
        min_length=2,
        max_length=40,
        regex="^[A-Za-z]+$")
    
    lastname: constr(min_length=2,
        max_length=40,
        regex="^[A-Za-z]+$")

    password: constr( 
        min_length=7,
        regex="^(?=.*[A-Z])(?=.*[0-9]).*$" )
    email: EmailStr



class UserValidationEdit(BaseModel):
    name: Optional[constr(
        min_length=2,
        max_length=40,
        regex="^[A-Za-z]+$")]
    
    lastname: Optional[constr(min_length=2,
        max_length=40,
        regex="^[A-Za-z]+$")]

    password: Optional[constr( 
        min_length=7,
        regex="^(?=.*[A-Z])(?=.*[0-9]).*$" )]
    email: Optional[EmailStr]



#                           ////////////////
#           VER TODOS LOS USUARIOS DE LA BASE DE DATOS
@app.get("/users")
async def users():
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    return users


@app.get("/")
async def saludo():
    return {"Hola":"Mundo"}



#           REGISTER
@app.post("/register")
async def registro(user: User ):
    VerifyUser(user.email,user.name)
    contraseña = Haspassword(user.password)
    
    cursor.execute(
        "INSERT INTO users (name, lastname, email, password) VALUES (%s, %s, %s, %s)",
        (user.name, user.lastname, user.email, contraseña))
    conn.commit()
    
    return {"message": "Se registro correctamente"}

#           LOGIN
@app.post("/login")
async def login(form: OAuth2PasswordRequestForm = Depends()):
    
    cursor.execute("SELECT email,password FROM users WHERE email=%s",[form.username])
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    
    if not crypt.verify(form.password,user[1]): 
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                            detail="The password is incorrect")
    
    access_token = {"sub":user[0],
                   "exp": datetime.utcnow() + timedelta(minutes=ACCES_TOKEN_DURATION)}

    return {"access_token": jwt.encode(access_token,SECRET,algorithm=ALGORITHM),"token_type": "bearer"}



# COMPRUEBA SI LA PERSONA SE LOGEO CORRECTAMENTE
async def comprobarToken(token: str = Depends(oauth2)):
    error = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales de autenticación inválidas",
        headers={"WWW-Authenticate": "Bearer"})
    
    try:
        username = jwt.decode(token,SECRET,algorithms=[ALGORITHM]).get("sub")
        if username is None:
            raise error
    except JWTError:
        raise error
    
    cursor.execute("SELECT name,lastname,email,id FROM users WHERE email=%s",[username])
    usernamee = cursor.fetchone()
    
    return usernamee

#  RETORNA INFORMACION DE USUARIO LOGEADO
@app.get("/users/me")
async def me(user: User = Depends(comprobarToken)):
    return user



# EDITA LA INFORMACION DE UN USUARIO
# EJEMPLO 
# http://127.0.0.1:8000/users/editUser/name?newdate=Aylen
@app.put("/users/editUser/{columnaName}")
async def editUsers(columnaName: str, newdate: str, user: User = Depends(comprobarToken)):
    diccio = {columnaName: newdate}
    validation = UserValidationEdit(columnaName=newdate)
    try:
        validation.validate(value=diccio)
    except ValueError as error:
        return {"ERROR": f"OCURRIO UN ERROR \n {error}"}
    if columnaName == "password":
        newdate = Haspassword(newdate)
        print(newdate)
 
    try:
        cursor.execute(f"UPDATE users SET {columnaName} = %s WHERE id = %s", [newdate, user[3]])
        conn.commit()
    except Exception as e:
        return {"ERROR": "OCURRIO UN ERROR CON LA BASE DE DATOS, INTENTELO MAS TARDE"}
    
    return {"Put": "Se actualizo correctamente el usuario"}
    
    


# Register administradores


