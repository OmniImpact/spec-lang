#! Package theojack:model
#! Blackjack round/match phase.

Enum is GamePhase{
	replace [String] is namespace: ['theojack', 'model'];

	BETTING,
	PLAYER_TURN,
	ROUND_OVER,
	MATCH_OVER
}
