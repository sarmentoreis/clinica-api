import asyncio
from models.models import User
from auth.security import get_password_hash
from database.connection import settings

async def criar_usuarios_iniciais():
    await settings.initialize_database()

    if await User.count() > 0:
        print("A base já possui usuários cadastrados. Cancelando operação.")
        return

    usuarios = [
        User(
            username="admin_leo",
            hashed_password=get_password_hash("senha123"),
            role="admin"
        ),
        User(
            username="dr_akira",
            hashed_password=get_password_hash("senha123"),
            role="profissional"
        ),
        User(
            username="recep_maria",
            hashed_password=get_password_hash("senha123"),
            role="recepcionista"
        )
    ]

    for user in usuarios:
        await user.insert()
        print(f"Usuário criado: {user.username} (Role: {user.role})")

    print("\nSeed finalizado! Use a senha 'senha123' para todos os usuários.")

if __name__ == "__main__":
    asyncio.run(criar_usuarios_iniciais())