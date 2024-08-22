import random

class Card:
    def __init__(self, rank):
        self.rank = rank

    def value(self):
        if self.rank in ['J', 'Q', 'K']:
            return 10
        elif self.rank == 'A':
            return 11
        else:
            return int(self.rank)

    def __repr__(self):
        return f"{self.rank}"

class Deck:
    def __init__(self, num_decks=6, cut_card_loc=0.75):
        self.num_decks = num_decks
        self.cut_card_loc = cut_card_loc
        self.shoe = self.create_deck()
        self.cut_card_position = int(len(self.shoe) * self.cut_card_loc)
        self.cut_card_reached_flag = False
        self.history = []

    def create_deck(self):
        values = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        deck = [Card(value) for value in values for _ in range(4 * self.num_decks)]
        random.shuffle(deck)
        return deck

    def draw_card(self):
        if len(self.shoe) == 0:
            self.reshuffle()
        if len(self.shoe) <= self.cut_card_position and not self.cut_card_reached_flag:
            self.cut_card_reached_flag = True
        card = self.shoe.pop()
        self.history.append(card)
        return card

    def cut_card_reached(self):
        return self.cut_card_reached_flag

    def reshuffle(self):
        self.shoe = self.create_deck()
        self.cut_card_position = int(len(self.shoe) * self.cut_card_loc)
        self.cut_card_reached_flag = False
        self.history = []

class Hand:
    def __init__(self):
        self.cards = []

    def add_card(self, card):
        self.cards.append(card)

    def value(self):
        total = sum(card.value() for card in self.cards)
        aces = sum(1 for card in self.cards if card.rank == 'A')
        while total > 21 and aces:
            total -= 10
            aces -= 1
        return total

    def is_pair(self):
        return len(self.cards) == 2 and self.cards[0].rank == self.cards[1].rank

    def is_soft_total(self):
        return any(card.rank == 'A' for card in self.cards) and self.value() <= 21

    def is_blackjack(self):
        return len(self.cards) == 2 and self.value() == 21

    def __repr__(self):
        return f"Hand({self.cards}, value={self.value()})"

class Player:
    def __init__(self, bankroll=1000, deck=None):
        self.hands = [Hand()]
        self.bankroll = bankroll
        self.current_bets = []
        self.deck = deck

    def place_bet(self, amount):
        self.current_bets.append(amount)
        self.bankroll -= amount  # Deduct the bet from bankroll when placed

    def payout(self, hand_index, multiplier):
        winnings = self.current_bets[hand_index] * multiplier
        self.bankroll += winnings  # Adjust the bankroll based on winnings or losses
        self.current_bets[hand_index] = 0  # Reset the bet for this hand

    def reset_hands(self):
        self.hands = [Hand()]
        self.current_bets = []

    def handle_double(self, hand_index=0): #
        self.current_bets[hand_index] *= 2
        return "double"

    def can_split(self, hand_index):
        hand = self.hands[hand_index]
        return hand.is_pair() and self.bankroll >= self.current_bets[hand_index]

    def split(self, hand_index):
        if not self.can_split(hand_index):
            raise ValueError("Cannot split this hand.")
        
        hand = self.hands[hand_index]
        split_card = hand.cards.pop()
        new_hand = Hand()
        new_hand.add_card(split_card)
        self.hands.append(new_hand)
        hand.add_card(self.deck.draw_card())
        new_hand.add_card(self.deck.draw_card())
        self.place_bet(self.current_bets[hand_index])
        return "split"

    def basic_strategy(self, dealer_upcard, hand_index=0):
        hand = self.hands[hand_index]
        if hand.is_pair():
            action = self.handle_pair(dealer_upcard, hand_index)
            return action
        elif hand.is_soft_total():
            return self.handle_soft_total(dealer_upcard, hand_index)
        else:
            return self.handle_hard_total(hand.value(), dealer_upcard, hand_index)

    def handle_soft_total(self, dealer_upcard, hand_index=0):
        hand_value = self.hands[hand_index].value()

        if hand_value in [13, 14]:  # Soft 13 or 14 (A,2 or A,3)
            if dealer_upcard in ['5', '6']:
                return self.handle_double(hand_index)
            else:
                return "hit"

        elif hand_value in [15, 16]:  # Soft 15 or 16 (A,4 or A,5)
            if dealer_upcard in ['4', '5', '6']:
                return self.handle_double(hand_index)
            else:
                return "hit"

        elif hand_value == 17:  # Soft 17 (A,6)
            if dealer_upcard in ['3', '4', '5', '6']:
                return self.handle_double(hand_index)
            else:
                return "hit"

        elif hand_value == 18:  # Soft 18 (A,7)
            if dealer_upcard in ['9', '10', 'A']:
                return "hit"
            elif dealer_upcard in ['3', '4', '5', '6']:
                return self.handle_double(hand_index)
            else:
                return "stay"

        elif hand_value == 19:  # Soft 19 (A,8)
            if dealer_upcard == '6':
                return self.handle_double(hand_index)
            else:
                return "stay"

        else:  # Soft 20 or higher (A,9 or A,10)
            return "stay"

    def handle_hard_total(self, hand_value, dealer_upcard, hand_index=0):
        if hand_value <= 8:
            return "hit"

        elif hand_value == 9:
            if dealer_upcard in ['3', '4', '5', '6']:
                return self.handle_double(hand_index)
            else:
                return "hit"

        elif hand_value == 10:
            if dealer_upcard not in ['10', 'A']:
                return self.handle_double(hand_index)
            else:
                return "hit"

        elif hand_value == 11:
            return self.handle_double(hand_index)

        elif hand_value == 12:
            if dealer_upcard in ['4', '5', '6']:
                return "stay"
            else:
                return "hit"

        elif 13 <= hand_value <= 16:
            if dealer_upcard in ['2', '3', '4', '5', '6']:
                return "stay"
            else:
                return "hit"

        else:  # hand_value >= 17
            return "stay"

    def handle_pair(self, dealer_upcard, hand_index=0):
        hand = self.hands[hand_index]
        pair_card = hand.cards[0].rank
        if pair_card == 'A':
            return self.split(hand_index)
        elif pair_card in ['8']:
            return self.split(hand_index)
        elif pair_card in ['2', '3', '7']:
            if dealer_upcard in ['2', '3', '4', '5', '6', '7']:
                return self.split(hand_index)
            else:
                return "hit"
        elif pair_card == '6' and dealer_upcard in ['2', '3', '4', '5', '6']:
            return self.split(hand_index)
        elif pair_card == '9':
            if dealer_upcard in ['7', '10', 'A']:
                return "stay"
            else:
                return self.split(hand_index)
        elif pair_card == '4' and dealer_upcard in ['5', '6']:
            return self.split(hand_index)
        else:
            return "stay"

class Game:
    def __init__(self, num_decks=6, num_hands=1, bet_size=10):
        self.deck = Deck(num_decks)
        self.player = Player(bankroll=1000, deck=self.deck)  # Only the player manages the bankroll
        self.dealer = Player(deck=self.deck)
        self.bet_size = bet_size
        self.num_hands = num_hands

    def play_hand(self):
        self.player.reset_hands()
        self.dealer.reset_hands()
        self.player.place_bet(self.bet_size)
        self.deal_initial_cards()

        print(f"Player's Hand: {self.player.hands[0]} vs Dealer's Upcard: {self.dealer.hands[0].cards[0]}")

        if self.check_blackjack_scenarios():
            return  # Exit if blackjack scenario is resolved

        self.player_actions()
        self.dealer_actions()
        self.resolve_hand()
        print(f"Dealer's Final Hand: {self.dealer.hands[0]}")

    def deal_initial_cards(self):
        for hand in self.player.hands:
            hand.add_card(self.deck.draw_card())
            hand.add_card(self.deck.draw_card())
        self.dealer.hands[0].add_card(self.deck.draw_card())
        self.dealer.hands[0].add_card(self.deck.draw_card())

    def check_blackjack_scenarios(self):
        player_blackjack = self.player.hands[0].is_blackjack()
        dealer_blackjack = self.dealer.hands[0].is_blackjack()

        if player_blackjack and dealer_blackjack:
            print("Push: Both player and dealer have blackjack")
            self.player.payout(0, 1)
            return True

        if dealer_blackjack:
            print("Dealer wins with blackjack")
            # No need to adjust bankroll further as the bet was already deducted
            return True

        if player_blackjack:
            print("Player wins with blackjack!")
            self.player.payout(0, 2.5)
            return True

        return False

    def player_actions(self):
        for hand_index, hand in enumerate(self.player.hands):
            action = self.player.basic_strategy(self.dealer.hands[0].cards[0].rank, hand_index)
            print(f"Action taken: {action} for hand {hand_index + 1}: {hand}")
            
            while action == "hit":
                hand.add_card(self.deck.draw_card())
                print(f"Hand after hit: {hand}")
                if hand.value() > 21:
                    print(f"Hand {hand_index + 1} busts with value: {hand.value()}")
                    break
                action = self.player.basic_strategy(self.dealer.hands[0].cards[0].rank, hand_index)
                print(f"Next action: {action} for hand {hand_index + 1}")

            if action == "double":
                hand.add_card(self.deck.draw_card())
                print(f"Hand after double: {hand}")
            elif action == "stay":
                print(f"Hand stays with value: {hand.value()}")

    def dealer_actions(self):
        while self.dealer.hands[0].value() < 17 or (self.dealer.hands[0].value() == 17 and self.dealer.hands[0].is_soft_total()):
            self.dealer.hands[0].add_card(self.deck.draw_card())

    def resolve_hand(self):
        dealer_final_value = self.dealer.hands[0].value()

        for i, hand in enumerate(self.player.hands):
            player_final_value = hand.value()
            if player_final_value > 21:
                print(f"Player's hand {i + 1} busts with value: {player_final_value}")
                # Bet is already deducted on placement, no further adjustment needed
            elif dealer_final_value > 21 or player_final_value > dealer_final_value:
                print(f"Player's hand {i + 1} wins with value: {player_final_value}")
                self.player.payout(i, 2)  # Payout is 2x the bet (initial bet + winnings)
            elif player_final_value == dealer_final_value:
                print(f"Player's hand {i + 1} pushes with value: {player_final_value}")
                self.player.payout(i, 1)  # Payout is 1x the bet (bet returned)
            else:
                print(f"Dealer wins against Player's hand {i + 1} with value: {dealer_final_value}")
                # Bet was already deducted, no need to adjust bankroll further

    def play_game(self):
        print(f"Starting Bankroll: ${self.player.bankroll}")
        for _ in range(self.num_hands):
            print("\n--- New Hand ---")
            self.play_hand()
            print(f"Bankroll after hand: ${self.player.bankroll}")
        
        # Final bankroll display
        print(f"\nFinal Bankroll after {self.num_hands} hands: ${self.player.bankroll}")

        # Print card history
        print("\nCard History:")
        for card in self.deck.history:
            print(card, end=" ")
        print()  # New line after printing all cards
        return self.player.bankroll
    
if __name__ == "__main__":
    # Initialize the game
    game = Game(num_decks=6, num_hands=5, bet_size=10)
    
    # Run the game
    final_bankroll = game.play_game()

    # Print the initial and final bankroll
    print(f"Initial Bankroll: $1000")
    print(f"Final Bankroll: ${final_bankroll}")