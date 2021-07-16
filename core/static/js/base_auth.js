$(document).ready(function(){
    const ws_scheme = window.location.protocol == 'https:' ? 'wss' : 'ws';
    const userUrl = 'u/' + username + '/';

    var userSocket;

    init();

    function updateConnections(data){
        var type = data.connection_state.connection_type,
			username = data.connection_state.user.username,
            block = data.connection_state.friend_block;

        $('#friend-' + username).remove();

		switch(type){
			case 'online':
				$(block).appendTo('#group-friends .side-panel-items-subgroup:nth-child(1)');

				break;
			case 'offline':
				$(block).appendTo('#group-friends .side-panel-items-subgroup:nth-child(2)');

				break;
			default:
				break;
		}
    }
    function updateNotifications(data){
        var notification = $(data.notification_block);

        console.log(data);

        switch(data.type){
            case 'room_invite':
                if ('room_url' in data)
                    window.location = data.room_url;
            case 'friend_add':
                $('#group-friends .side-panel-items-subgroup:nth-child(' + (data.friend_online ? '1' : '2') + ')').append(data.friend_block);

                $('.notification-id[value="' + data.notification_id + '"]').parents('.notification').remove()

                break;
            case 'friend_remove':
                $('#friend-' + data.friend_username).remove();
                $('#friend-' + data.friend_username).remove();
            default:
                break;
        }

        if ('notification_id' in data)
            $('.notification-id[value="' + data.notification_id + '"]').parents('.notification').remove();

        $('#temp-notifications').append(notification);

        if (data.permanent){
            $('#notification-list').append(data.notification_block);

            var notificationCount = parseInt($('#notification-badge p').text());

            $('#notification-badge p').text(notificationCount + 1)

            $('#notification-badge').addClass('show');
        }

        setTimeout(function(){
            notification.remove();
        }, 5000);
    }

    function sendFriendRequest(customQuery){
        var query = (customQuery == null || customQuery.length == 0) ? $('#add-friend input').val() : customQuery;

        $.ajax({
            url: '/friend/request',
            type: 'GET',
            data: {
                query: query,
            },
            success: function(data){
                console.log(data);
            },
            failure: function(e){
                console.log('failure');
            }
        });
    }

    function init(){
        Array.prototype.remove = function(from, to) {
            var rest = this.slice((to || from) + 1 || this.length);
            this.length = from < 0 ? this.length + from : from;
            return this.push.apply(this, rest);
          };

        userSocket = new WebSocket(ws_scheme + '://' + window.location.host + '/ws/' + userUrl);
        
        registerConnection(userSocket, 'online', 'Online Services', ws_scheme + '://' + window.location.host + '/ws/' + userUrl, function(newSocket){
            userSocket = newSocket;
        });

        userSocket.onmessage = function(e){
			const data = JSON.parse(e.data);
			
			console.log(data);
			
			switch(data.type){
				case 'connection':
					updateConnections(data.response_data.data);

					break;
                case 'notification':
                    updateNotifications(data.response_data.data);
				default:
					break;
			}
		}
    }

    $('.profile-picture-icon').each(function(){
        $(this).width($(this).height());
    });

    $(document).on('click', ':not(.popup-element)', function(e){
        var div = this;

        $('.popup-container:not(.barebones)').each(function(){
            var toggle = $(this).find('.popup-toggle'),
                element = $(this).find('.popup-element');

            var target = $(div).parents('.popup-container')[0] == $(this)[0] || $(div)[0] == $(this)[0];

            if (target && ($(div).hasClass('popup-element') || $(div).parents('.popup-element').length > 0))
                return;

            if (target && ($(div).hasClass('popup-toggle') || $(div).parents('.popup-toggle').length > 0)){
                if (element.css('visibility') == 'visible'){
                    $(this).removeClass('open');

                    element.css({
                        'visibility': 'hidden',
                        'opacity': '0'
                    });
                } else {
                    $(this).addClass('open');

                    element.css({
                        'visibility': 'visible',
                        'opacity': '1'
                    });
                }
            } else {
                $(this).removeClass('open');

                element.css({
                    'visibility': 'hidden',
                    'opacity': '0'
                });
            }
        });

        e.stopPropagation();
    });

    $('#close-message').on('click', function(){
        $('#user-message-container').css('display', 'none');
    });

    $('.message img').on('click', function(){
        $(this).parent().remove();

        if ($('#messages-container').children().length == 0){
            $('#messages-container').remove();
        }
    });

    $('.side-panel-items-controller').on('mouseenter', function(){
        $(this).find('.popup-element').addClass('open');
    });
    $('.side-panel-items-controller .popup-element').on('mouseleave', function(){
        $(this).removeClass('open');
    });

    $('.selector-option').hover(function(){
        var id = $(this).prop('id'),
            text = '';

        if (id == 'selector-friends'){
            text = 'Friends';
        } else {
            text = 'Room Users';
        }

        $(this).parents('.popup-element').find('.item-label').text(text);
    });
    $('.selector-option').on('click', function(){
        var id = $(this).prop('id'),
            name = id.split('selector-')[1];

        if (id == 'selector-friends'){
            $(this).parents('.popup-container').find('.popup-toggle img').attr('src', $(this).find('img').attr('src'));
        } else {
            $(this).parents('.popup-container').find('.popup-toggle img').attr('src', $(this).find('img').attr('src'));
        }

        $(this).appendTo($(this).parents('.selector-options'));

        $(this).parents('.popup-element').removeClass('open');

        $('#right-side-panel .side-panel-items-group').removeClass('selected');
        $('#group-' + name).addClass('selected');
    });

    $(document).on('click', '.notification-action, .notification-action *', function(){
        var accept = true,
            notificationDiv = $(this).parents('.notification'),
            notificationId = notificationDiv.find('.notification-id').val();

        if ($(this).hasClass('notification-action')){
            if ($(this).hasClass('close')){
                notificationDiv.remove();

                return;
            }

            accept = $(this).hasClass('accept');
        } else if ($(this).parents('.notification-action').hasClass('close')){
            notificationDiv.remove();

            return;
        } else
            accept = $(this).parents('.notification-action').hasClass('accept');

        $.ajax({
            url: '/notification/',
            type: 'POST',
            data: {
                notification_id: notificationId,
                accept: accept
            },
            success: function(data){
                console.log(data);

                var notificationCount = parseInt($('#notification-badge p').text());

                if (notificationCount > 1)
                    $('#notification-badge p').text(notificationCount - 1);
                else{
                    $('#notification-badge p').text('0');
                    
                    $('#notification-badge').removeClass('show');
                }

                notificationDiv.remove();
            },
            failure: function(e){
                console.log('failure');
            }
        });
    });

    $('#add-friend input').on('keypress', function(e){
        if (e.which == 13){
            sendFriendRequest();
        }
    });
    $('#add-friend .preview-option.accept').on('click', sendFriendRequest);

    $(document).on('click', '.preview-option.remove-friend, .preview-option.remove-friend *', function(){
        var username = $(this).parents('.popup-container').find('input[name="username"]').val();

        $.ajax({
            url: '/friend/remove/',
            type: 'POST',
            data: {
                username: username
            },
            success: function(data){
                console.log(data);
            },
            failure: function(e){
                console.log('failure');
            }
        });
    });
    $(document).on('click', '.preview-option.add-friend, .preview-option.add-friend *', function(){
        var username = $(this).parents('.popup-container').find('input[name="username"]').val();

        sendFriendRequest(username);
    });
    $(document).on('click', '.preview-option.room-invite, .preview-option.room-invite *', function(){
        var username = $(this).parents('.popup-container').find('input[name="username"]').val(),
            roomCode = $(this).parents('.popup-container').find('input[name="room-code"]').val();

        $.ajax({
            url: '/room/invite/',
            type: 'POST',
            data: {
                username: username,
                room_code: roomCode
            },
            success: function(data){
                console.log(data);
            },
            failure: function(e){
                console.log('failure');
            }
        });
    });
});

var connections = [], connectionCount = 0;

function registerConnection(socket, code, name, url, callback){
    connections.push({
        'socket': socket,
        'code': code,
        'name': name,
        'url': url,
        'callback': callback
    });

    $('.connection.' + code).remove();

    var template = $('.connection.template').clone();
    template.find('.connection-name').text(name);
    template.removeClass('template');
    template.addClass(code);

    template.insertBefore('.connection.template');

    socket.onopen = function(e){
        var i;

        for (i = 0; i < connections.length; i++){
            var connection = connections[i];

            if (connection.socket == socket){
                $('.connection.' + connection.code).removeClass('disconnected');
                $('.connection.' + connection.code).addClass('connected');

                $('.connection.' + connection.code + ' .connection-icon img.disconnected').hide();
                $('.connection.' + connection.code + ' .connection-icon img.connected').show();

                break;
            }
        }

        connectionCount++;

        updateConnectionStatus();
    };
    socket.onclose = function(e){
        var i, connection;

        for (i = 0; i < connections.length; i++){
            connection = connections[i];

            if (connection.socket == socket){
                $('.connection.' + connection.code).removeClass('connected');
                $('.connection.' + connection.code).addClass('disconnected');

                $('.connection.' + connection.code + ' .connection-icon img.connected').hide();
                $('.connection.' + connection.code + ' .connection-icon img.disconnected').show();

                connections.remove(i);

                break;
            }
        }

        reconnectTimer = setTimeout(function(){
            socket = new WebSocket(connection.url);

            registerConnection(socket, connection.code, connection.name, connection.url, connection.callback);

            connection.callback(socket);
        }, 5000);

        connectionCount--;

        updateConnectionStatus();
    };
}
function updateConnectionStatus(){
    var image = $('#connection-container .popup-toggle img'), src = image.attr('src');

    if (connectionCount == 0){
        $('#connection-container').removeClass('connected');
        $('#connection-container').removeClass('mixed');
        $('#connection-container').addClass('disconnected');

        $('#connection-container .popup-toggle img.connected').hide();
        $('#connection-container .popup-toggle img.disconnected').show();
        $('.connection.' + connection.code + ' .connection-icon img.disconnected').show();
    } else if (connectionCount == connections.length){
        $('#connection-container').removeClass('disconnected');
        $('#connection-container').removeClass('mixed');
        $('#connection-container').addClass('connected');

        $('#connection-container .popup-toggle img.disconnected').hide();
        $('#connection-container .popup-toggle img.connected').show();
    } else {
        $('#connection-container').removeClass('disconnected');
        $('#connection-container').removeClass('connected');
        $('#connection-container').addClass('mixed');

        $('#connection-container .popup-toggle img.disconnected').hide();
        $('#connection-container .popup-toggle img.connected').show();
    }
}