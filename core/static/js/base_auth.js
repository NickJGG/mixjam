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

    $(document).on('click', '*', function(e){
        var div = $(e.target),
            isElement = div.hasClass('dropdown-element') || div.parents('.dropdown-element').length > 0,
            isToggle = div.hasClass('dropdown-toggle') || div.parents('.dropdown-toggle').length > 0;
        
        var container = $(this).parents('.dropdown-container').first(),
            toggle = container.find('.dropdown-toggle').first(),
            inContainer = container.length > 0;
        
        var group = container.find('.dropdown-group').first().val(),
            layer = parseInt(container.find('.dropdown-layer').first().val());

        if (!isElement || isToggle){
            if (inContainer){
                container.toggleClass('open');
                toggle.toggleClass('selected');

                $('.dropdown-container').each(function(){
                    var otherGroup = $(this).find('.dropdown-group').first().val(),
                        otherLayer = parseInt($(this).find('.dropdown-layer').first().val()),
                        otherToggle = $(this).find('.dropdown-toggle').first();
                
                    if (group == otherGroup && layer <= otherLayer){
                        var otherContainer = $(this);

                        if (otherContainer[0] != container[0]){
                            otherContainer.removeClass('open');
                            otherToggle.removeClass('selected');
                        }
                    }
                });
            } else{
                $('.dropdown-container').removeClass('open');
                $('.dropdown-container .dropdown-toggle').removeClass('selected');
            }

            e.stopPropagation();
        } else if (isElement){
            div.find('.dropdown-container').each(function(){
                var otherLayer = parseInt($(this).find('.dropdown-layer').val());
            
                if (layer <= otherLayer){
                    var otherContainer = $(this);

                    if (otherContainer[0] != container[0]){
                        otherContainer.removeClass('open');
                    }
                }
            });

            var isClose = div.hasClass('dropdown-close') || div.parents('.dropdown-close').length > 0;

            if (isClose){
                container.removeClass('open');
                toggle.removeClass('selected');
            }

            e.stopPropagation();
        }
    });

    $(document).on('click', '#song-info, #song-info *, #mobile-player .dropdown-close, #mobile-player .dropdown-close *', function(){
        $('body').addClass('disabled');
    });
    $(document).on('click', '#mobile-player .dropdown-close, #mobile-player .dropdown-close *', function(){
        $('body').removeClass('disabled');
    });
});

var connections = [];

function registerConnection(socket, code, name, url, callback){
    connections.push({
        'socket': socket,
        'code': code,
        'name': name,
        'url': url,
        'callback': callback
    });

    var connectionElement = $('#connection-' + code);

    connectionElement.addClass('open');
    connectionElement.addClass('connecting');
    
    connectionElement.find('.connection-status').text('Connecting...');

    socket.onopen = function(e){
        var i;

        for (i = 0; i < connections.length; i++){
            var connection = connections[i];

            if (connection.socket == socket){
                connectionElement.addClass('connected');
                connectionElement.removeClass('connecting');
                connectionElement.find('.connection-status').text('Connected');

                break;
            }
        }

        updateConnectionStatus();
    };
    socket.onclose = function(e){
        var i, connection;

        for (i = 0; i < connections.length; i++){
            connection = connections[i];

            if (connection.socket == socket){
                connectionElement.removeClass('connected');
                connectionElement.find('.connection-status').text('Disconnected');

                connections.remove(i);

                break;
            }
        }

        reconnectTimer = setTimeout(function(){
            socket = new WebSocket(connection.url);

            registerConnection(socket, connection.code, connection.name, connection.url, connection.callback);

            connection.callback(socket);
        }, 5000);

        updateConnectionStatus();
    };
}
function updateConnectionStatus(){
    var totalConnections = $('.connection.open').length,
        connectedCount = $('.connection.connected').length;

    if (connectedCount == 0){
        $('#connection-container').removeClass('connected');
        $('#connection-container').removeClass('mixed');
    } else if (connectedCount == totalConnections){
        $('#connection-container').removeClass('mixed');
        $('#connection-container').addClass('connected');
    } else {
        $('#connection-container').removeClass('connected');
        $('#connection-container').addClass('mixed');
    }
}