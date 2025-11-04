from .authority_games_mesa_az import Authority_Games_Mesa_Arizona
from .game_kastle_santa_clara import Game_Kastle_Santa_Clara
from .sun_valley_gaming import SunValleyGaming

# Instantiate all store scraper classes
authority_games = Authority_Games_Mesa_Arizona()
game_kastle_sc = Game_Kastle_Santa_Clara()
sun_valley = SunValleyGaming()

# The registry maps store slugs to their implementation instances.
# This is the single source of truth for all available stores.
STORE_REGISTRY = {
    authority_games.slug: authority_games,
    game_kastle_sc.slug: game_kastle_sc,
    sun_valley.slug: sun_valley,
    # Add other stores here as they are implemented
}
