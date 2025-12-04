from sqlalchemy import Column, Integer, String, Boolean, DateTime, BigInteger, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base
from sqlalchemy.dialects.postgresql import UUID

class Questionnaire(Base):
    __tablename__ = "questionnaires"

    id = Column(BigInteger, primary_key=True, index=True)
    created_on = Column(DateTime(timezone=True))
    modified_on = Column(DateTime(timezone=True))
    active = Column(Boolean, nullable=False)
    name = Column(String(200), nullable=False)
    condition = Column(String(2000), nullable=False, default="0")
    end_screen = Column(String(200), nullable=False, default="home")
    owner = Column(UUID(as_uuid=True))
    modified_by = Column(UUID(as_uuid=True))
    penhas_start_automatically = Column(Boolean, nullable=False, default=True)
    penhas_cliente_required = Column(Boolean, nullable=False, default=True)

class ClientesQuizSession(Base):
    __tablename__ = "clientes_quiz_session"

    id = Column(BigInteger, primary_key=True, index=True)
    cliente_id = Column(BigInteger, ForeignKey("clientes.id"), nullable=False)
    questionnaire_id = Column(BigInteger, ForeignKey("questionnaires.id"), nullable=False)
    finished_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    stash = Column(JSON, default={})
    responses = Column(JSON, default={})
    deleted_at = Column(DateTime(timezone=True))
    deleted = Column(Boolean, nullable=False, default=False)

    cliente = relationship("Cliente")
    questionnaire = relationship("Questionnaire")


class AnonymousQuizSession(Base):
    """
    Anonymous quiz sessions (no user required)
    Port from AnonymousQuizSession.pm
    """
    __tablename__ = "anonymous_quiz_session"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    token = Column(String(200), nullable=False, unique=True, index=True)
    questionnaire_id = Column(BigInteger, ForeignKey("questionnaires.id"), nullable=False)
    finished_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    stash = Column(JSON, default={})
    responses = Column(JSON, default={})
    remote_ip = Column(String(100), nullable=True)

    questionnaire = relationship("Questionnaire")


class QuizConfig(Base):
    """
    Quiz configuration
    Port from QuizConfig.pm
    """
    __tablename__ = "quiz_config"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    config_key = Column(String(200), nullable=False, unique=True)
    config_value = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class MfQuestionnaireOrder(Base):
    """
    Manual de Fuga questionnaire ordering
    Port from MfQuestionnaireOrder.pm
    """
    __tablename__ = "mf_questionnaire_order"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    questionnaire_id = Column(BigInteger, ForeignKey("questionnaires.id"), nullable=False, index=True)
    sort_order = Column(Integer, nullable=False, default=0)
    active = Column(Boolean, nullable=False, default=True)

    questionnaire = relationship("Questionnaire")


class MfQuestionnaireRemoveTarefa(Base):
    """
    Manual de Fuga questionnaire task removal configuration
    Port from MfQuestionnaireRemoveTarefa.pm
    """
    __tablename__ = "mf_questionnaire_remove_tarefa"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    questionnaire_id = Column(BigInteger, ForeignKey("questionnaires.id"), nullable=False, index=True)
    mf_tarefa_id = Column(BigInteger, ForeignKey("mf_tarefas.id"), nullable=False, index=True)

    questionnaire = relationship("Questionnaire")
    mf_tarefa = relationship("MfTarefa")

