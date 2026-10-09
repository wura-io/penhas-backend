-- Broadcast a message from "Suporte PenhaS" to every active user via the support chat.
-- PRODUCTION version (RDS penhas_prod, Perl API + Directus schema).
-- For the staging Python backend use broadcast_support_message.staging.sql.
--
-- Mirrors Penhas::Helpers::ChatSupport::support_send_message (admin branch):
--   1. ensure a chat_support room exists for each user
--   2. insert a chat_support_message with admin_user_id = directus_users.id (uuid)
--      (the Perl API only looks at admin_user_id to set is_me = 0)
--   3. update the room's last_msg_* columns (last_msg_is_support = true)
--   4. (optional) queue a push notification in chat_clientes_notifications
--
-- Usage (admin_user_id is required: a directus_users uuid):
--   psql "$DB_URL" -v admin_user_id=8d7daf63-1ca2-49aa-9a55-9bae2addf688 -f scripts/broadcast_support_message.prod.sql
--
-- The script ends with ROLLBACK by default. Check the counts, then change it to COMMIT.
-- Re-running is safe: users who already have this exact message from an admin are skipped.

\set ON_ERROR_STOP on

\if :{?admin_user_id}
\else
\echo 'missing -v admin_user_id=<directus_users uuid>'
\quit
\endif

BEGIN;

-- the admin who "sends" the message (shown as last_msg_by in the admin panel)
CREATE TEMP TABLE _bc_admin ON COMMIT DROP AS
SELECT id, coalesce(nullif(first_name, ''), 'PenhaS') AS first_name
FROM directus_users
WHERE id = :'admin_user_id'
  AND status = 'active';

DO $$
BEGIN
    IF (SELECT count(*) FROM _bc_admin) <> 1 THEN
        RAISE EXCEPTION 'admin not found (needs an active directus_users id)';
    END IF;
END $$;

-- target users + rendered message
CREATE TEMP TABLE _bc_target ON COMMIT DROP AS
SELECT
    c.id AS cliente_id,
    replace(
$tpl$Olá, {{name}}! Como você está?
Temos um comunicado super importante a fazer e precisamos da sua atenção.
Para garantir uma experiência cada vez melhor aqui no PenhaS, pedimos que as usuárias mantenham o aplicativo sempre atualizado. Por isso, pedimos que verifique se há uma nova versão disponível na loja de aplicativos do seu celular (Play Store ou App Store). Se aparecer a opção “Atualizar”, é só clicar e aguardar que a atualização seja concluída.
Alguns modelos de celular fazem a atualização automaticamente, mas é importante conferir. E assim você pode continuar aproveitando da melhor forma todos os recursos e melhorias disponíveis no PenhaS.
Contamos com você. Um abraço carinhoso.$tpl$,
        '{{name}}',
        coalesce(
            nullif(initcap(split_part(trim(c.nome_completo), ' ', 1)), ''),
            nullif(trim(c.apelido), ''),
            'usuária'
        )
    ) AS message
FROM clientes c
WHERE c.status = 'active'
  AND NOT c.eh_admin;

-- 1. create missing support rooms
INSERT INTO chat_support (cliente_id, last_msg_at, created_at)
SELECT t.cliente_id, now(), now()
FROM _bc_target t
ON CONFLICT (cliente_id) DO NOTHING;

-- skip users who already received this exact message (idempotency)
DELETE FROM _bc_target t
USING chat_support cs
JOIN chat_support_message m ON m.chat_support_id = cs.id
WHERE cs.cliente_id = t.cliente_id
  AND m.admin_user_id IS NOT NULL
  AND m.message = t.message;

-- 2. insert the messages
INSERT INTO chat_support_message (cliente_id, chat_support_id, message, admin_user_id, created_at)
SELECT t.cliente_id, cs.id, t.message, a.id, now()
FROM _bc_target t
JOIN chat_support cs ON cs.cliente_id = t.cliente_id
CROSS JOIN _bc_admin a;

-- 3. update the rooms
UPDATE chat_support cs
SET last_msg_is_support = true,
    last_msg_at         = now(),
    last_msg_preview    = CASE WHEN length(t.message) > 100
                               THEN substr(t.message, 1, 100) || '…'
                               ELSE t.message END,
    last_msg_by         = a.first_name
FROM _bc_target t, _bc_admin a
WHERE cs.cliente_id = t.cliente_id;

-- 4. queue push notifications (comment out to send silently)
--    Maintenance tick picks up rows older than 5 min, 100 per run (~every 10s).
--    rows already pushed (notification_created) would block a new push, so replace them
DELETE FROM chat_clientes_notifications n
USING _bc_target t
WHERE n.cliente_id = t.cliente_id
  AND n.pending_message_cliente_id = -1
  AND n.notification_created;

INSERT INTO chat_clientes_notifications (cliente_id, messaged_at, pending_message_cliente_id)
SELECT t.cliente_id, now(), -1
FROM _bc_target t
WHERE NOT EXISTS (
    SELECT 1 FROM chat_clientes_notifications n
    WHERE n.cliente_id = t.cliente_id
      AND n.pending_message_cliente_id = -1
);

-- sanity checks
SELECT id AS admin_id, first_name AS sender FROM _bc_admin;
SELECT count(*) AS users_targeted FROM _bc_target;
SELECT
    (SELECT count(*) FROM chat_support)                                         AS rooms_total,
    (SELECT count(*) FROM chat_support_message WHERE created_at = now())        AS messages_inserted,
    (SELECT count(*) FROM chat_clientes_notifications WHERE messaged_at = now()) AS notifications_queued;
SELECT t.cliente_id, left(t.message, 60) AS preview FROM _bc_target t ORDER BY t.cliente_id LIMIT 5;

ROLLBACK;
-- COMMIT;
