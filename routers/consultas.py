from fastapi import APIRouter, HTTPException, Request, Depends, status, Security
from fastapi.templating import Jinja2Templates
from models.models import *
from auth import security
from database.connection import Database
from beanie import PydanticObjectId

router = APIRouter(
    prefix="/consultas",
    tags=["Consultas"]
)

templates = Jinja2Templates(directory="templates")

consulta_db = Database(Consulta)

@router.get("/", response_model=list[ConsultaResponse])
async def listar_consultas(current_user: User = Security(security.get_current_user, scopes=["consultas:read"])):
    if current_user.role in ["admin", "laboratorio"]:
        return await consulta_db.get_all()

    return await Consulta.find(Consulta.profissional_nome == current_user.username).to_list()

@router.get("/view", include_in_schema=False)
async def visualizar_agenda_html(request: Request):
    consultas = await consulta_db.get_all()
    return templates.TemplateResponse(
        request=request,
        name="agenda.html",
        context={"request": request, "consultas": consultas}
    )


@router.post("/", response_model=ConsultaResponse, status_code=status.HTTP_201_CREATED)
async def criar_consulta(consulta: ConsultaCreate, current_user: User = Security(security.get_current_user, scopes=["consultas:write"])):
    nova_consulta = Consulta(
        paciente_nome=consulta.paciente_nome,
        data_hora=consulta.data_hora,
        status="agendada",
        profissional_nome=current_user.username,
        token_auditoria=f"AUDIT-CREATED-BY-{current_user.username}"
    )

    await consulta_db.save(nova_consulta)

    return nova_consulta

@router.get("/{consulta_id}", response_model=ConsultaResponse)
async def obter_consulta(consulta_id: PydanticObjectId, current_user: User = Security(security.get_current_user, scopes=["consultas:read"])):
    consulta = await consulta_db.get(consulta_id)
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta não encontrada")

    if current_user.role not in ["admin", "laboratorio"] and consulta.profissional_nome != current_user.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Acesso negado. Você só pode visualizar as consultas dos seus próprios pacientes."
        )
    return consulta

@router.delete("/limpar", dependencies=[Security(security.get_current_user, scopes=["consultas:write"]), Depends(security.require_admin)])
async def limpar_todas_consultas():
    await Consulta.delete_all() 
    return {"message": "Base de consultas formatada com sucesso."}