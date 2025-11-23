import pytest

from app.main import create_app
from app.core.database import db
from app.models.game import Game
from app.models.player import Player
from app.models.product import ProductRecipe, PlayerProduct


@pytest.fixture
def app():
    """Create a fresh app with in-memory SQLite for each test."""
    app = create_app(config_overrides={
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SQLALCHEMY_ECHO": False,
        "TESTING": True,
    })

    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def app_ctx(app):
    """Provide an application context for tests that need direct DB access."""
    with app.app_context():
        yield app


@pytest.fixture
def two_players(app_ctx):
    """Create a game with two active players."""
    game = Game(room_code="TEST01", status="in_progress", current_round=1, max_players=4)
    db.session.add(game)
    db.session.flush()

    p1 = Player(game_id=game.id, nickname="P1", player_number=1, turn_order=1, cash=10000)
    p2 = Player(game_id=game.id, nickname="P2", player_number=2, turn_order=2, cash=10000)
    db.session.add_all([p1, p2])
    db.session.commit()
    return game, p1, p2


@pytest.fixture
def make_recipe(app_ctx):
    """Factory to create a recipe."""
    created = []

    def _make(name="测试奶茶", difficulty=3, base_fan_rate=5.0, recipe_json=None):
        recipe = ProductRecipe(
            name=f"{name}-{len(created)}",
            difficulty=difficulty,
            base_fan_rate=base_fan_rate,
            cost_per_unit=10.0,
            recipe_json=recipe_json or {"milk": 1, "tea": 1},
            is_active=True,
        )
        db.session.add(recipe)
        db.session.commit()
        created.append(recipe)
        return recipe

    return _make


@pytest.fixture
def unlock_product(app_ctx):
    """Factory to create/unlock a PlayerProduct for a player and recipe."""
    def _unlock(player_id, recipe_id, price=None, total_sold=0, ad_score=0, unlocked_round=1):
        product = PlayerProduct(
            player_id=player_id,
            recipe_id=recipe_id,
            is_unlocked=True,
            unlocked_round=unlocked_round,
            total_sold=total_sold,
            current_price=price,
            current_ad_score=ad_score,
        )
        db.session.add(product)
        db.session.commit()
        return product

    return _unlock
