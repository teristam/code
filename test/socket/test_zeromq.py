import pytest
from unittest.mock import MagicMock, patch
import zmq
from GUI.image_socket import Image_socket

@pytest.fixture
def mock_zmq_context():
    with patch('zmq.Context') as mock_context:
        yield mock_context

@pytest.fixture
def mock_camera_widget():
    return MagicMock()

def test_init_binds_sockets(mock_zmq_context, mock_camera_widget):
    mock_context_instance = MagicMock()
    mock_zmq_context.return_value = mock_context_instance
    pub_socket = MagicMock()
    pull_socket = MagicMock()
    mock_context_instance.socket.side_effect = [pub_socket, pull_socket]

    pub_address = 'tcp://127.0.0.1:5555'
    pull_address = 'tcp://127.0.0.1:5556'
    sock = Image_socket(mock_camera_widget, pub_address, pull_address)

    mock_context_instance.socket.assert_any_call(zmq.PUB)
    mock_context_instance.socket.assert_any_call(zmq.PULL)
    pub_socket.bind.assert_called_once_with(pub_address)
    pull_socket.bind.assert_called_once_with(pull_address)
    assert sock.pub_socket is pub_socket
    assert sock.pull_address is pull_socket


def test_send_calls_send_multipart(mock_zmq_context, mock_camera_widget):
    mock_context_instance = MagicMock()
    mock_zmq_context.return_value = mock_context_instance
    pub_socket = MagicMock()
    pull_socket = MagicMock()
    mock_context_instance.socket.side_effect = [pub_socket, pull_socket]
    sock = Image_socket(mock_camera_widget, 'tcp://127.0.0.1:5555', 'tcp://127.0.0.1:5556')

    topic = b'test_topic'
    metadata = b'meta'
    image = b'img'
    sock.send(topic, metadata, image)
    pub_socket.send_multipart.assert_called_once_with([topic, metadata, image])


def test_get_receives_json(mock_zmq_context, mock_camera_widget):
    mock_context_instance = MagicMock()
    mock_zmq_context.return_value = mock_context_instance
    pub_socket = MagicMock()
    pull_socket = MagicMock()
    mock_context_instance.socket.side_effect = [pub_socket, pull_socket]
    sock = Image_socket(mock_camera_widget, 'tcp://127.0.0.1:5555', 'tcp://127.0.0.1:5556')

    pull_socket.poll.return_value = True
    pull_socket.recv_json.return_value = {'foo': 'bar'}
    result = sock.get(timeout=100)
    assert result == {'foo': 'bar'}
    pull_socket.poll.assert_called_once_with(timeout=100)
    pull_socket.recv_json.assert_called_once()


def test_get_returns_none_on_zmq_again(mock_zmq_context, mock_camera_widget):
    mock_context_instance = MagicMock()
    mock_zmq_context.return_value = mock_context_instance
    pub_socket = MagicMock()
    pull_socket = MagicMock()
    mock_context_instance.socket.side_effect = [pub_socket, pull_socket]
    sock = Image_socket(mock_camera_widget, 'tcp://127.0.0.1:5555', 'tcp://127.0.0.1:5556')

    pull_socket.poll.side_effect = zmq.Again
    result = sock.get(timeout=100)
    assert result is None


def test_close_closes_sockets_and_context(mock_zmq_context, mock_camera_widget):
    mock_context_instance = MagicMock()
    mock_zmq_context.return_value = mock_context_instance
    pub_socket = MagicMock()
    pull_socket = MagicMock()
    mock_context_instance.socket.side_effect = [pub_socket, pull_socket]
    sock = Image_socket(mock_camera_widget, 'tcp://127.0.0.1:5555', 'tcp://127.0.0.1:5556')

    sock.close()
    pub_socket.close.assert_called_once()
    pull_socket.close.assert_called_once()
    mock_context_instance.term.assert_called_once()
