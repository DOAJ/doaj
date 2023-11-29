from redis import StrictRedis
from unittest.mock import patch, Mock, MagicMock
from doajtest.helpers import DoajTestCase
from portality.events.system_status_check import KafkaStatusCheck
import portality.events.kafka_producer as kafka_events
class TestKafkaStatusCheck(DoajTestCase):

    def setUp(self):
        super(TestKafkaStatusCheck, self).setUp()
        self.kafka_status = KafkaStatusCheck()

    @patch.object(StrictRedis, "get", return_value=b'True')
    @patch.object(KafkaStatusCheck, "can_check_redis", return_value=True)
    def test_active_status(self, mock_kafka_status_check, mock_strict_redis):
        status = self.kafka_status.is_active()
        self.assertTrue(status)
        mock_kafka_status_check.assert_called_once()
        mock_strict_redis.assert_called_once()

    @patch.object(StrictRedis, "get", return_value=b'False')
    @patch.object(KafkaStatusCheck, "can_check_redis", return_value=True)
    def test_inactive_status(self, mock_kafka_status_check, mock_strict_redis):
        status = self.kafka_status.is_active()
        self.assertFalse(status)
        mock_kafka_status_check.assert_called_once()
        mock_strict_redis.assert_called_once()

class TestKafkaProducer(DoajTestCase):

    # Test for handle_exception
    @patch('portality.core.app.logger.exception')
    @patch('portality.app_email.send_mail')
    def test_handle_exception(self, mock_send_mail, mock_logger_exception):
        error_msg = "Sample error"
        exception = Exception("Sample exception")
        kafka_events.handle_exception(error_msg, exception)

        mock_logger_exception.assert_called_once_with(error_msg + str(exception))
        mock_send_mail.assert_called_once()

    # Test for kafka_producer when producer is None and no exception raised
    @patch('kafka.KafkaProducer')
    def test_kafka_producer_new(self, mock_kafka_producer):
        kafka_events.producer = None
        result = kafka_events.kafka_producer()

        self.assertIsNotNone(result)
        mock_kafka_producer.assert_called_once()

    # Test for kafka_producer when producer is already set
    def test_kafka_producer_existing(self):
        kafka_events.producer = Mock()
        result = kafka_events.kafka_producer()

        self.assertEqual(result, kafka_events.producer)

    # Test for kafka_producer when exception raised
    @patch('kafka.KafkaProducer', side_effect=Exception("Kafka error"))
    @patch('portality.events.kafka_producer.handle_exception')
    def test_kafka_producer_exception(self, mock_handle_exception, _):
        kafka_events.producer = None
        result = kafka_events.kafka_producer()

        self.assertIsNone(result)
        mock_handle_exception.assert_called_once()

    # Test for send_event when kafka_status is None
    @patch('portality.events.kafka_producer.shortcircuit_send_event')
    def test_send_event_status_none(self, mock_shortcircuit_send_event):
        kafka_events.kafka_status = None

        kafka_events.send_event(Mock())
        mock_shortcircuit_send_event.assert_called_once()

    # Test for send_event when everything is operational
    @patch.object(KafkaStatusCheck, 'is_active', return_value=True)
    @patch('portality.events.kafka_producer.kafka_producer', return_value=Mock())
    @patch('portality.events.shortcircuit')
    def test_send_event_operational(self, mock_shortcircuit, _, __):
        kafka_events.kafka_status = KafkaStatusCheck()

        kafka_events.send_event(Mock())
        mock_shortcircuit.assert_not_called()

    # Test for send_event when exception occurs
    @patch('kafka.KafkaProducer',  return_value=Mock(send=MagicMock(side_effect=Exception("Send error"))))
    @patch.object(KafkaStatusCheck, 'set_kafka_inactive_redis')
    @patch.object(KafkaStatusCheck, 'is_active', return_value=True)
    @patch('portality.events.kafka_producer.shortcircuit_send_event')
    @patch('portality.events.kafka_producer.handle_exception')
    @patch('portality.events.kafka_producer.producer', new=None)
    def test_send_event_exception(self, __, mock_handle_exception, mock_shortcircuit, _, mock_kafka_producer):
        kafka_events.kafka_status = KafkaStatusCheck()

        kafka_events.send_event(Mock())
        mock_handle_exception.assert_called()
        mock_shortcircuit.assert_called_once()
        mock_kafka_producer.assert_called_once()
