from sqlalchemy import Column, Integer, String, Boolean, DateTime, BigInteger, Text, ForeignKey, SmallInteger
from sqlalchemy.orm import relationship, backref
from datetime import datetime
from app.db.base_class import Base

class Tweet(Base):
    __tablename__ = "tweets"

    id = Column(String(20), primary_key=True) # Manual ID generation required
    status = Column(String(20), nullable=False, default="draft")
    content = Column(Text)
    parent_id = Column(String(20), ForeignKey("tweets.id"))
    anonimo = Column(Boolean, nullable=False, default=False)
    qtde_reportado = Column(BigInteger, default=0)
    qtde_expansoes = Column(BigInteger, default=0)
    qtde_likes = Column(BigInteger, nullable=False, default=0)
    qtde_comentarios = Column(BigInteger, default=0)
    escondido = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True))
    cliente_id = Column(BigInteger, ForeignKey("clientes.id"), nullable=False)
    ultimo_comentario_id = Column(String(20))
    media_ids = Column(Text)
    disable_escape = Column(Boolean, nullable=False, default=False)
    tags_index = Column(String(5000), nullable=False, default=",,")
    original_parent_id = Column(String(20))
    tweet_depth = Column(SmallInteger, nullable=False, default=1)
    use_penhas_avatar = Column(Boolean, nullable=False, default=False)

    cliente = relationship("Cliente")
    parent = relationship("Tweet", remote_side=[id], backref=backref("replies", lazy="dynamic"))
    likes = relationship("TweetLikes", back_populates="tweet")
    reports = relationship("TweetsReport", back_populates="tweet")

class TweetLikes(Base):
    __tablename__ = "tweets_likes"

    id = Column(BigInteger, primary_key=True, index=True)
    created_on = Column(DateTime(timezone=True), default=datetime.utcnow)
    cliente_id = Column(BigInteger, ForeignKey("clientes.id"), nullable=False)
    tweet_id = Column(String(20), ForeignKey("tweets.id"), nullable=False)

    cliente = relationship("Cliente")
    tweet = relationship("Tweet", back_populates="likes")

class TweetsReport(Base):
    __tablename__ = "tweets_reports"

    id = Column(BigInteger, primary_key=True, index=True)
    cliente_id = Column(BigInteger, ForeignKey("clientes.id"), nullable=False)
    reported_id = Column(String(20), ForeignKey("tweets.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    reason = Column(String(200), nullable=False)

    cliente = relationship("Cliente")
    tweet = relationship("Tweet", back_populates="reports")

