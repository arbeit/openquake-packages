================
 Change history
================

.. _version-1.2.1:

1.2.1
=====
:release-date: TBA

* Now depends on amqplib >= 1.0.0.

* Redis: Now automatically deletes auto_delete queues at ``basic_cancel``.

* ``serialization.unregister`` added so it is possible to remove unwanted
  seralizers.

* Fixes MemoryError while importing ctypes on SELinux (Issue #52).

* ``BrokerConnection.autoretry`` is a version of ``ensure`` that works
  with arbitrary functions (i.e. it does not need an associated object
  that implements the ``revive`` method.

  Example usage:

  .. code-block:: python

        channel = connection.channel()
        try:
            ret, channel = connection.autoretry(send_messages, channel=channel)
        finally:
            channel.close()

* ``ConnectionPool.acquire`` no longer force establishes the connection.

    The connection will be established as needed.

* ``BrokerConnection.ensure`` now supports an ``on_revive`` callback
  that is applied whenever the connection is re-established.

* ``Consumer.consuming_from(queue)`` returns True if the Consumer is
  consuming from ``queue``.

* ``Consumer.cancel_by_queue`` did not remove the queue from ``queues``.

* ``compat.ConsumerSet.add_queue_from_dict`` now automatically declared
  the queue if ``auto_declare`` set.

.. _version-1.2.0:

1.2.0
=====
:release-date: 2011-07-15 12:00 P.M BST

* Virtual: Fixes cyclic reference in Channel.close (Issue #49).

* Producer.publish: Can now set additional properties using keyword
  arguments (Issue #48).

* Adds Queue.no_ack option to control the no_ack option for individual queues.

* Recent versions broke pylibrabbitmq support.

* SimpleQueue and SimpleBuffer can now be used as contexts.

* Test requirements specifies PyYAML==3.09 as 3.10 dropped Python 2.4 support

* Now properly reports default values in Connection.info/.as_uri

.. _version-1.1.6:

1.1.6
=====
:release-date: 2011-06-13 04:00 P.M BST

* Redis: Fixes issue introduced in 1.1.4, where a redis connection
  failure could leave consumer hanging forever.

* SQS: Now supports fanout messaging by using SimpleDB to store routing
  tables.

    This can be disabled by setting the `supports_fanout` transport option:

        >>> BrokerConnection(transport="SQS",
        ...                  transport_options={"supports_fanout": False})

* SQS: Now properly deletes a message when a message is acked.

* SQS: Can now set the Amazon AWS region, by using the ``region``
  transport option.

* amqplib: Now uses `localhost` as default hostname instead of raising an
  error.

.. _version-1.1.5:

1.1.5
=====
:release-date: 2011-06-07 06:00 P.M BST

* Fixes compatibility with redis-py 2.4.4.

.. _version-1.1.4:

1.1.4
=====
:release-date: 2011-06-07 04:00 P.M BST

* Redis transport: Now requires redis-py version 2.4.4 or later.

* New Amazon SQS transport added.

    Usage:

        >>> conn = BrokerConnection(transport="SQS",
        ...                         userid=aws_access_key_id,
        ...                         password=aws_secret_access_key)

    The environment variables :envvar:`AWS_ACCESS_KEY_ID` and
    :envvar:`AWS_SECRET_ACCESS_KEY` are also supported.

* librabbitmq transport: Fixes default credentials support.

* amqplib transport: Now supports `login_method` for SSL auth.

    :class:`BrokerConnection` now supports the `login_method`
    keyword argument.

    Default `login_method` is ``AMQPLAIN``.

.. _version-1.1.3:

1.1.3
=====
:release-date: 2011-04-21 16:00 P.M CEST

* Redis: Consuming from multiple connections now works with Eventlet.

* Redis: Can now perform channel operations while the channel is in
  BRPOP/LISTEN mode (Issue #35).

    Also the async BRPOP now times out after 1 second, this means that
    cancelling consuming from a queue/starting consuming from additional queues
    has a latency of up to one second (BRPOP does not support subsecond
    timeouts).

* Virtual: Allow channel objects to be closed multiple times without error.

* amqplib: ``AttributeError`` has been added to the list of known
  connection related errors (:attr:`Connection.connection_errors`).

* amqplib: Now converts :exc:`SSLError` timeout errors to
  :exc:`socket.timeout` (http://bugs.python.org/issue10272)

* Ensures cyclic references are destroyed when the connection is closed.

.. _version-1.1.2:

1.1.2
=====
:release-date: 2011-04-06 16:00 P.M CEST

* Redis: Fixes serious issue where messages could be lost.

    The issue could happen if the message exceeded a certain number
    of kilobytes in size.

    It is recommended that all users of the Redis transport should
    upgrade to this version, even if not currently experiencing any
    issues.

.. _version-1.1.1:

1.1.1
=====
:release-date: 2011-04-05 15:51 P.M CEST

* 1.1.0 started using ``Queue.LifoQueue`` which is only available
  in Python 2.6+ (Issue #33).  We now ship with our own LifoQueue.


.. _version-1.1.0:

1.1.0
=====
:release-date: 2011-04-05 01:05 P.M CEST

.. _v110-important:

Important Notes
---------------

* Virtual transports: Message body is now base64 encoded by default
  (Issue #27).

    This should solve problems sending binary data with virtual
    transports.

    Message compatibility is handled by adding a ``body_encoding``
    property, so messages sent by older versions is compatible
    with this release.  However -- If you are accessing the messages
    directly not using Kombu, then you have to respect
    the ``body_encoding`` property.

    If you need to disable base64 encoding then you can do so
    via the transport options::

        BrokerConnection(transport="...",
                         transport_options={"body_encoding": None})

    **For transport authors**:

        You don't have to change anything in your custom transports,
        as this is handled automatically by the base class.

        If you want to use a different encoder you can do so by adding
        a key to ``Channel.codecs``.  Default encoding is specified
        by the ``Channel.body_encoding`` attribute.

        A new codec must provide two methods: ``encode(data)`` and
        ``decode(data)``.

* ConnectionPool/ChannelPool/Resource: Setting ``limit=None`` (or 0)
  now disables pool semantics, and will establish and close
  the resource whenever acquired or released.

* ConnectionPool/ChannelPool/Resource: Is now using a LIFO queue
  instead of the previous FIFO behavior.

    This means that the last resource released will be the one
    acquired next.  I.e. if only a single thread is using the pool
    this means only a single connection will ever be used.

* BrokerConnection: Cloned connections did not inherit transport_options
  (``__copy__``).

* contrib/requirements is now located in the top directory
  of the distribution.

* MongoDB: Now supports authentication using the ``userid`` and ``password``
  arguments to :class:`BrokerConnection` (Issue #30).

* BrokerConnection: Default autentication credentials are now delegated to
  the individual transports.
 
    This means that the ``userid`` and ``password`` arguments to
    BrokerConnection is no longer *guest/guest* by default.

    The amqplib and pika transports will still have the default
    credentials.

* :meth:`Consumer.__exit__` did not have the correct signature (Issue #32).

* Channel objects now have a ``channel_id`` attribute.

* MongoDB: Version sniffing broke with development versions of
	mongod (Issue #29).

* New environment variable :envvar:`KOMBU_LOG_CONNECTION` will now emit debug
  log messages for connection related actions.

  :envvar:`KOMBU_LOG_DEBUG` will also enable :envvar:`KOMBU_LOG_CONNECTION`.

.. _version-1.0.7:

1.0.7
=====
:release-date: 2011-03-28 05:45 P.M CEST

* Now depends on anyjson 0.3.1

    cjson is no longer a recommended json implementation, and anyjson
    will now emit a deprecation warning if used.

* Please note that the Pika backend only works with version 0.5.2.

    The latest version (0.9.x) drastically changed API, and it is not
    compatible yet.

* on_decode_error is now called for exceptions in message_to_python
  (Issue #24).

* Redis: did not respect QoS settings.

* Redis: Creating a connection now ensures the connection is established.

    This means ``BrokerConnection.ensure_connection`` works properly with
    Redis.

* consumer_tag argument to ``Queue.consume`` can't be :const:`None`
  (Issue #21).

    A None value is now automatically converted to empty string.
    An empty string will make the server generate a unique tag.

* BrokerConnection now supports a ``transport_options`` argument.

    This can be used to pass additional arguments to transports.

* Pika: ``drain_events`` raised :exc:`socket.timeout` even if no timeout
  set (Issue #8).

.. version-1.0.6:

1.0.6
=====
:release-date: 2011-03-22 04:00 P.M CET

* The ``delivery_mode`` aliases (persistent/transient) were not automatically
  converted to integer, and would cause a crash if using the amqplib
  transport.

* Redis: The redis-py :exc:`InvalidData` exception suddenly changed name to
  :exc:`DataError`.

* The :envvar:`KOMBU_LOG_DEBUG` environment variable can now be set to log all
  channel method calls.

  Support for the following environment variables have been added:

    * :envvar:`KOMBU_LOG_CHANNEL` will wrap channels in an object that
      logs every method call.

    * :envvar:`KOMBU_LOG_DEBUG` both enables channel logging and configures the
      root logger to emit messages to standard error.

    **Example Usage**::

        $ KOMBU_LOG_DEBUG=1 python
        >>> from kombu import BrokerConnection
        >>> conn = BrokerConnection()
        >>> channel = conn.channel()
        Start from server, version: 8.0, properties:
            {u'product': 'RabbitMQ',..............  }
        Open OK! known_hosts []
        using channel_id: 1
        Channel open
        >>> channel.queue_declare("myq", passive=True)
        [Kombu channel:1] queue_declare('myq', passive=True)
        (u'myq', 0, 1)

.. _version-1.0.5:

1.0.5
=====
:release-date: 2011-03-17 04:00 P.M CET

* Fixed memory leak when creating virtual channels.  All virtual transports
  affected (redis, mongodb, memory, django, sqlalchemy, couchdb, beanstalk).

* Virtual Transports: Fixed potential race condition when acking messages.

    If you have been affected by this, the error would show itself as an
    exception raised by the OrderedDict implementation. (``object no longer
    exists``).

* MongoDB transport requires the ``findandmodify`` command only available in
  MongoDB 1.3+, so now raises an exception if connected to an incompatible
  server version.

* Virtual Transports: ``basic.cancel`` should not try to remove unknown
  consumer tag.

.. _version-1.0.4:

1.0.4
=====
:release-date: 2011-02-28 04:00 P.M CET

* Added Transport.polling_interval

    Used by django-kombu to increase the time to sleep between SELECTs when
    there are no messages in the queue.

    Users of django-kombu should upgrade to django-kombu v0.9.2.

.. _version-1.0.3:

1.0.3
=====
:release-date: 2011-02-12 04:00 P.M CET

* ConnectionPool: Re-connect if amqplib connection closed

* Adds ``Queue.as_dict`` + ``Exchange.as_dict``.

* Copyright headers updated to include 2011.

.. _version-1.0.2:

1.0.2
=====
:release-date: 2011-01-31 10:45 P.M CET

* amqplib: Message properties were not set properly.
* Ghettoq backend names are now automatically translated to the new names.

.. _version-1.0.1:

1.0.1
=====
:release-date: 2011-01-28 12:00 P.M CET

* Redis: Now works with Linux (epoll)

.. _version-1.0.0:

1.0.0
=====
:release-date: 2011-01-27 12:00 P.M CET

* Initial release

.. _version-0.1.0:

0.1.0
=====
:release-date: 2010-07-22 04:20 P.M CET

* Initial fork of carrot
