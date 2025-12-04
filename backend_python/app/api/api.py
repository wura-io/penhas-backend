from fastapi import APIRouter

from app.api.endpoints import (
    login, users, pontos_apoio, news, guardioes, quiz, chat, onboarding, 
    timeline, settings, media, admin, admin_stats, tarefas, preferences, 
    badges, faq, notifications, audio, maintenance, admin_panel, public, anon_quiz
)

api_router = APIRouter()
# Public endpoints (no auth required)
api_router.include_router(public.router, prefix="", tags=["public"])
api_router.include_router(anon_quiz.router, prefix="/anon-questionnaires", tags=["anon-quiz"])
api_router.include_router(login.router, tags=["login"])
api_router.include_router(onboarding.router, prefix="", tags=["onboarding"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(settings.router, prefix="", tags=["settings"])
api_router.include_router(pontos_apoio.router, prefix="/pontos-de-apoio", tags=["pontos-de-apoio"])
api_router.include_router(news.router, prefix="/news", tags=["news"])
api_router.include_router(guardioes.router, prefix="/guardioes", tags=["guardioes"])
api_router.include_router(quiz.router, prefix="/quiz", tags=["quiz"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(timeline.router, prefix="/timeline", tags=["timeline"])
api_router.include_router(media.router, prefix="", tags=["media"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(admin_stats.router, prefix="/admin", tags=["admin-stats"])
api_router.include_router(admin_panel.router, prefix="/admin-panel", tags=["admin-panel"])
api_router.include_router(tarefas.router, prefix="/me/tarefas", tags=["tarefas"])
api_router.include_router(preferences.router, prefix="/me/preferences", tags=["preferences"])
api_router.include_router(badges.router, prefix="/badge", tags=["badges"])
api_router.include_router(faq.router, prefix="/web/faq", tags=["faq"])
api_router.include_router(notifications.router, prefix="/me/notifications", tags=["notifications"])
api_router.include_router(audio.router, prefix="/me/audios", tags=["audio"])
api_router.include_router(maintenance.router, prefix="/maintenance", tags=["maintenance"])
