from .start import router_start
from .echo import router_echo
from .new_player import router_new_player
from .new_game import router_add_game
from .all_players import router_all_players
from .players import router_players
from .all_games import router_all_games
from .message import router_message
from .my_stats import router_my_stats
from .general_stats import router_general_stats
from .new_chat import router_new_chat
from .delete_player import router_delete_player


routers = [
    router_start, router_new_player,
    router_all_players, router_delete_player,
    router_add_game, router_all_games,
    router_message, router_my_stats,
    router_general_stats, router_new_chat,
    router_players, router_echo]
