import unittest
from unittest import mock

from utils import ai_helper


def reply(status: int, text: str = "", retry_after: str | None = None) -> mock.Mock:
    response = mock.Mock(status_code=status, headers={"retry-after": retry_after} if retry_after else {})
    response.json.return_value = {"choices": [{"message": {"content": text}}]}
    response.raise_for_status.side_effect = None if status == 200 else Exception(f"HTTP {status}")
    return response


@mock.patch.object(ai_helper, "GROQ_API_KEY", "test-key")
@mock.patch.object(ai_helper.time, "sleep")
class ChatResponseTests(unittest.TestCase):
    def test_sends_history_and_page_data_and_returns_the_reply(self, _sleep):
        history = [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}]
        with mock.patch.object(ai_helper.requests, "post", return_value=reply(200, "answer")) as post:
            self.assertEqual(ai_helper.chat_response(history, "Why?", "PAGE: Main Dashboard"), "answer")
        messages = post.call_args.kwargs["json"]["messages"]
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[1:3], history)
        self.assertIn("PAGE: Main Dashboard", messages[3]["content"])

    def test_waits_and_retries_once_when_rate_limited(self, sleep):
        with mock.patch.object(ai_helper.requests, "post",
                               side_effect=[reply(429, retry_after="3"), reply(200, "answer")]):
            self.assertEqual(ai_helper.chat_response([], "Why?"), "answer")
        sleep.assert_called_once_with(3.0)

    def test_failure_returns_a_safe_message(self, _sleep):
        with mock.patch.object(ai_helper.requests, "post", side_effect=[reply(429), reply(429)]), \
                self.assertLogs(ai_helper.logger, "ERROR"):
            self.assertIn("could not be generated", ai_helper.chat_response([], "Why?"))


if __name__ == "__main__":
    unittest.main()
