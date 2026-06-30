import bcrypt

usuarios = {
    "juan.perez":  "password123",   # colaborador_general
    "ana.gomez":   "password123",   # mando_medio
    "carlos.vega": "password123",   # comercial_senior
    "lucia.rios":  "password123",   # tecnico_senior
    "admin":       "password123",   # gerencia
}

for user, pwd in usuarios.items():
    h = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()
    print(f'"{user}": {{"password_hash": "{h}", "rol": "..."}},')