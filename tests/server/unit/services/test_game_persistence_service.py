import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from server.database.sqlite_db_manager import SQLiteDBManager, GameHistoryModel
from shared.message_contracts.contracts import GameFinishedPayload
from services.game_persistence_service.app import handle_game_finished
from services.game_server.app import handle_game_over_nats
from server.services.server_event_bus import ServerEvent, ServerEventType
from server.network.models import GameRoom, ConnectedPlayer
from shared.protocol import GameOverMessage


def test_sqlite_db_save_game_history():
    db = SQLiteDBManager(db_path="sqlite:///:memory:")
    success = db.save_game_history(
        room_id="room_999",
        winner="white",
        reason="checkmate",
        final_ratings={"Alice": 1220, "Bob": 1180}
    )
    assert success is True

    with db._get_session() as session:
        records = session.query(GameHistoryModel).filter(GameHistoryModel.room_id == "room_999").all()
        assert len(records) == 1
        assert records[0].winner == "white"
        assert records[0].reason == "checkmate"
        assert "Alice" in records[0].final_ratings


def test_handle_game_finished_subscriber():
    async def _test():
        payload = GameFinishedPayload(
            room_id="room_abc",
            winner="black",
            reason="resignation",
            final_ratings={"Player1": 1150, "Player2": 1250}
        )

        with patch("services.game_persistence_service.app.db_manager.save_game_history") as mock_save:
            mock_save.return_value = True
            await handle_game_finished(payload)
            mock_save.assert_called_once_with(
                room_id="room_abc",
                winner="black",
                reason="resignation",
                final_ratings={"Player1": 1150, "Player2": 1250}
            )

    asyncio.run(_test())


def test_handle_game_over_nats_publishing():
    async def _test():
        p1 = ConnectedPlayer(ws=None, ip_address="127.0.0.1")
        p1.username = "Alice"
        p2 = ConnectedPlayer(ws=None, ip_address="127.0.0.1")
        p2.username = "Bob"

        room = GameRoom("room_777")
        room.white_player = p1
        room.black_player = p2

        over_msg = GameOverMessage(winner="white", reason="elimination", white_rating=1216, black_rating=1184)
        event = ServerEvent(event_type=ServerEventType.GAME_OVER, target=room, data=over_msg)

        with patch("services.game_server.app.nats_bus.publish", new_callable=AsyncMock) as mock_pub:
            await handle_game_over_nats(event)
            assert mock_pub.called
            subject, dto = mock_pub.call_args[0]
            assert subject == "game.finished"
            assert isinstance(dto, GameFinishedPayload)
            assert dto.room_id == "room_777"
            assert dto.winner == "white"
            assert dto.final_ratings == {"Alice": 1216, "Bob": 1184}

    asyncio.run(_test())
