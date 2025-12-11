# test_brute.py
import pytest
from brute import Brute


def describe_Brute():
    # ----- bruteOnce tests (NO test doubles) -----
    def describe_bruteOnce():
        def it_returns_true_when_attempt_matches_target():
            secret = "Abc123"
            brute = Brute(secret)
            assert brute.bruteOnce(secret) is True

        def it_returns_false_when_attempt_does_not_match_target():
            brute = Brute("Abc123")
            assert brute.bruteOnce("wrong") is False

        def it_handles_min_and_max_length_passwords():
            # edge-case lengths: 1 and 8 characters
            brute1 = Brute("a")
            brute8 = Brute("Abc12345")  # 8 chars
            assert brute1.bruteOnce("a") is True
            assert brute8.bruteOnce("Abc12345") is True

        @pytest.mark.parametrize(
            "secret, attempt, expected",
            [
                ("a", "a", True),                  # min length
                ("Abc12345", "Abc12345", True),    # max password
                ("Password!", "Password!", True),  # punctuation
                ("Case", "case", False),           # case sensitive
                ("1234", "123", False),            # shorter attempt
                ("1234", "12345", False),          # longer attempt
            ],
        )
        def it_compares_various_passwords_correctly(secret, attempt, expected):
            brute = Brute(secret)
            assert brute.bruteOnce(attempt) is expected

    # ----- bruteMany tests (USE test doubles + mocks) -----
    def describe_bruteMany():
        def it_returns_seconds_when_cracked_before_limit(mocker):
            brute = Brute("secret")

            # stub randomGuess: first wrong, then correct
            mocker.patch.object(
                brute,
                "randomGuess",
                side_effect=["xxx", "secret"],
            )

            # control time.time so result is deterministic
            mocker.patch(
                "brute.time.time",
                side_effect=[100.0, 100.5],
            )

            result = brute.bruteMany(limit=5)
            assert result == 0.5  # success path

        def it_returns_minus_one_when_not_cracked_within_limit(mocker):
            brute = Brute("secret")

            # randomGuess NEVER returns the correct password
            mocker.patch.object(brute, "randomGuess", return_value="xxx")

            # time isn't super important here, but we stub it anyway
            mocker.patch(
                "brute.time.time",
                side_effect=[200.0, 200.2],
            )

            result = brute.bruteMany(limit=3)
            assert result == -1  # failure path

        def it_uses_randomGuess_and_bruteOnce_until_success(mocker):
            brute = Brute("secret")

            # stub randomGuess to take 3 attempts
            guess_stub = mocker.patch.object(
                brute,
                "randomGuess",
                side_effect=["a", "b", "secret"],
            )

            # spy on bruteOnce to verify how it is called
            brute_once_spy = mocker.spy(brute, "bruteOnce")

            # stub time so it doesn't actually sleep
            mocker.patch("brute.time.time", side_effect=[0.0, 1.0])

            brute.bruteMany(limit=10)

            # verify implementation details via mocks
            assert guess_stub.call_count == 3
            assert brute_once_spy.call_count == 3
            brute_once_spy.assert_called_with("secret")

        def it_respects_the_limit_when_zero(mocker):
            brute = Brute("secret")

            # edge case: limit = 0 → loop never runs
            guess_stub = mocker.patch.object(brute, "randomGuess")

            mocker.patch("brute.time.time", return_value=10.0)
            result = brute.bruteMany(limit=0)

            assert result == -1
            guess_stub.assert_not_called()

        def it_succeeds_if_guess_on_last_allowed_attempt(mocker):
            brute = Brute("secret")
            limit = 5

            # 4 wrong guesses, then correct on the 5th (= last allowed)
            guesses = ["w1", "w2", "w3", "w4", "secret"]
            guess_stub = mocker.patch.object(
                brute,
                "randomGuess",
                side_effect=guesses,
            )

            mocker.patch("brute.time.time", side_effect=[0.0, 1.0])

            result = brute.bruteMany(limit=limit)

            assert result == 1.0
            assert guess_stub.call_count == limit

        def it_fails_if_secret_would_be_guessed_after_limit(mocker):
            brute = Brute("secret")
            limit = 3

            # 3 allowed attempts (all wrong), then "secret" which should never be used
            guesses = ["a", "b", "c", "secret"]
            guess_stub = mocker.patch.object(
                brute,
                "randomGuess",
                side_effect=guesses,
            )

            mocker.patch("brute.time.time", side_effect=[10.0, 10.2])

            result = brute.bruteMany(limit=limit)

            assert result == -1
            # ensure we didn't go past limit
            assert guess_stub.call_count == limit

        def it_treats_negative_limit_like_zero(mocker):
            brute = Brute("secret")
            guess_stub = mocker.patch.object(brute, "randomGuess")

            mocker.patch("brute.time.time", return_value=42.0)
            result = brute.bruteMany(limit=-5)

            assert result == -1
            guess_stub.assert_not_called()
