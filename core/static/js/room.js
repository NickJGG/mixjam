$(document).ready(function(){

	/////////////////////////////////////////////////////////////////////////////////////
	//                                                                                 //
	//                                    VARIABLES                                    //
	//                                                                                 //
	/////////////////////////////////////////////////////////////////////////////////////

	const ws_scheme = window.location.protocol == 'https:' ? 'wss' : 'ws';
	const roomUrl = 'r/' + code + '/', userUrl = 'u/' + username + '/';
	
	var socket, timer, seek = false, movingProgress = false;
	var historyEntries = [], historyUpper = 4000, historyLower = 2000, historyTransition = 200, displayHistoryEntry = true;
	var deviceActive;
	
	init();
	
// 	#region Main Functions

	function updateDevices(data){
		var devices = data['response_data']['devices'],
			volume = data['response_data']['volume'];

		deviceActive = data['response_data']['active'];

		$('#device-list').empty();

		if (devices != null){
			devices.forEach(function(device){
				$('#device-list').append(device);
			});
		}

		if (deviceActive){
			$('#devices-image').addClass('active').removeClass('inactive');
			$('#volume-image').addClass('active').removeClass('inactive');

			$('#volume-container').find('.progress-complete').css({
				'height': 'calc(' + (volume) + '%)'
			});
		} else {
			$('#devices-image').removeClass('active').addClass('inactive');
			$('#volume-image').removeClass('active').addClass('inactive');

			$('#volume-container').css('display', 'none');
		}
	}

	function updateActivity(data){
		var action = data['response_data']['action'],
			action_data = data['response_data']['action_data'];

		switch (action){
			default:
				break;
		}
	}

	function updateUserAction(data){
		var action = data['response_data']['action'];

		switch(action){
			case 'profile':
				var block = data['response_data']['block'];

				$('#users-overlay').css('display', 'flex');
				$('#users-overlay .overlay-content').empty();

				$('#users-overlay .overlay-content').append(block);

				break;
			case 'leave':
				var username = data['response_data']['action_data']['user'];

				$('#user-' + username).remove();

				$('#user-online-count').text($('#user-list').children().length);
				$('#user-offline-count').text($('#offline-user-list').children().length);

				break;
			default:
				break;
		}
	}

	function updateHistory(data){
		var block = data['response_data']['data']['block'],
			action = data['response_data']['data']['request_action'];

		block = $(block);

		switch(action){
			case 'seek':
				block.append(`
					<div class = "entry-object lone">
						` + secondsToClock(roomState.song_state.progress_ms / 1000).split('.')[0] + `
					</div>
				`);

				break;
			case 'next':
			case 'previous':
			case 'play_direct':
				block.append(`
					<div class = "entry-image">
						<img src = "` + roomState.song_state.track.album.images[2].url + `">
					</div>
					<p class = "entry-object">
						` + roomState.song_state.track.name + `
					</p>
				`);

				break;
			default:
				break;
		}

		var length = historyEntries.push(block);

		$('#history-entry-list').prepend(block.clone());

		if (displayHistoryEntry){
			startHistoryEntry();
		}
	}
	function startHistoryEntry(){
		displayHistoryEntry = false;

		var block = historyEntries.shift();

		$('#history-entries').empty();
		$('#history-entries').append(block);
		$('.history-entry').animate({
			'opacity': '1'
		}, historyTransition);

		var length = historyEntries.length > 0 ? historyLower : historyUpper;

		setTimeout(hideHistoryEntry, length);
	}
	function hideHistoryEntry(){
		$('#hdistory-entries .history-entry').each(function(){
			$(this).animate({
				'opacity': '0'
			}, historyTransition);
		});

		setTimeout(showNextHistoryEntry, historyTransition);
	}
	function showNextHistoryEntry(){
		if (historyEntries.length > 0)
			startHistoryEntry();
		else {
			displayHistoryEntry = true;

			$('#history-entries').empty();
		}
	}

	function updateAdmin(data){
		var action = data['response_data']['action'],
			successful = data['response_data']['successful'];

		if (action == 'kick'){
			if (successful)
				location.href = '/';
		} else if (action == 'delete'){
			location.href = '/';
		}
	}

	function updateChat(data){
		var action = data['response_data']['action'],
			text = data['response_data']['action_data']['text'],
			username = data['response_data']['action_data']['user']['username'],
			messageColor = data['response_data']['action_data']['user']['color'],
			self = data['response_data']['action_data']['user']['self'],
			newMessage = true;
		
		if ($('#chat-messages').children().length > 0){
			var lastMessage = $('.chat-message').last();

			if ($(lastMessage).find('.message-username').text() == username){
				$(lastMessage).find('.chat-message-string').append(`
					<div class = "chat-message-text">
						` + text + `
					</div>
				`);

				newMessage = false;
			}
		}

		if (newMessage){
			$('#chat-messages').append(`
				<div class = "chat-message ` + (self ? 'self' : '') + `">
					<div class = "chat-message-info">
						<div class = "message-color" style = "--message-color: #` + messageColor + `"></div>
						<p class = "message-username">` + username + `</p>
					</div>
					<div class = "chat-message-string">
						<div class = "chat-message-text">
							` + text + `
						</div>
					</div>
				</div>
			`);
		}

		$('#chat-messages-wrapper').scrollTop($('#chat-messages-wrapper')[0].scrollHeight);

		if (!$('#tab-label-chat').hasClass('selected')){
			$('#unread-count').text(parseInt($('#unread-count').text()) + 1);
			$('#unread-count').css('display', 'block');
		}
	}

	function updatePlaylist(){
		const songState = roomState.song_state,
			  playlistState = roomState.playlist_state;
		
		seek = !movingProgress;

		$('#song-image img').prop('src', songState.track.album.images[2].url);
		$('#current-song-name').text(songState.track.name);
		$('#current-song-artist').text(songState.track.artists[0].name);
		
		var timeLeft = songState.track.duration_ms - songState.progress_ms;
		
		playing = songState.is_playing;
		
		startTimer(timeLeft, function(){
			
		});
				
		updatePlayButton();
		updateProgress();
		
		if (playlistState != null){
			var imageIndex = playlistState.images.length > 1 ? 1 : 0;

			$('#playlist-cover img').prop('src', playlistState.images[imageIndex].url);
			$('#playlist-title').text(playlistState.name);
			$('#playlist-song-count').text(playlistState.tracks.total);
			
			$('#song-list-wrapper').empty();
			
			$('.song.playing').removeClass('playing');
			
			var i, length = 0;
			
			for (i = 0; i < playlistState.tracks.items.length; i++){
				var song = playlistState.tracks.items[i],
					songPlaying = song.track.name == songState.track.name;
				
				length += song.track.duration_ms;
				
				/*$('#playlist-songs').append(`<div class = "playlist-song ` + (songPlaying ? 'playing' : '') + `">
												<div style = "display: flex; align-items: center;">
													<img class = "song-cover" src = "` + song.track.album.images[2].url + `">
													<p class = "song-title">` + song.track.name + `</p>
												</div>
												<p class = "song-artist">` + song.track.artists[0].name + `</p>
												<p class = "song-album">` + song.track.album.name + `</p>
												<p class = "song-user">` + song.added_by.id + `</p>
												<p class = "song-length">` + secondsToClock(Math.round(song.track.duration_ms / 1000.0)) + `</p>
											</div>`);*/

				var songElement = $(roomState.song_block);
				songElement.find('.song-cover > img').attr('src', song.track.album.images[2].url);
				songElement.find('.song-title').text(song.track.name);
				songElement.find('.song-artist').text(song.track.artists[0].name);
				songElement.find('.song-album p').text(song.track.album.name);
				songElement.find('.song-link').attr('href', song.track.external_urls.spotify);

				if (songPlaying)
					songElement.addClass('playing');
				
				$('#song-list-wrapper').append(songElement);
			}
			
			$('#playlist-length').text(secondsToLength(length / 1000));
		}
	}
	function updateConnections(data){
		var type = data.response_data.data.connection_state.connection_type,
			username = data.response_data.data.connection_state.user.username,
			self_kicked = data.response_data.data.connection_state.self_kicked;

		console.log(self_kicked);

		switch(type){
			case 'join':
				$('#user-' + username).remove();

				$('#group-users .side-panel-items-subgroup:nth-child(1)').append(data.response_data.data.connection_state.user.user_block);

				break;
			case 'leave':
				$('#user-' + username).remove();

				$('#group-users .side-panel-items-subgroup:nth-child(2)').append(data.response_data.data.connection_state.user.user_block);

				break;
			case 'kick':
				$('#user-' + username).remove();

				break;
			default:
				break;
		}
	}
	
// 	#endregion

// 	#region Initialization
	
	function init(){
		setupSocket();
		setupControls();
		fixTimes();
	}
	
	function setupSocket(){
		socket = new WebSocket(ws_scheme + '://' + window.location.host + '/ws/' + roomUrl);

		registerConnection(socket, 'room', 'Room Services', ws_scheme + '://' + window.location.host + '/ws/' + roomUrl, function(newSocket){
			socket = newSocket;
		});

		socket.onmessage = function(e){
			const data = JSON.parse(e.data);
			
			console.log(data);
			
			switch(data.type){
				case 'connection':
					updateConnections(data);

					break;
				case 'playlist':
					roomState = data.response_data;

					updatePlaylist();

					break;
				case 'chat':
					updateChat(data);

					break;
				case 'admin':
					updateAdmin(data);

					break;
				case 'request_history':
				case 'history_entry':
					updateHistory(data);

					break;
				case 'user_action':
					updateUserAction(data);

					break;
				case 'activity':
					updateActivity(data);

					break;
				case 'devices':
					updateDevices(data);

					break;
				default:
					break;
			}
		}
	}
	function setupControls(){
		$('.song-control').on('click', function(){
			var id = $(this).attr('id'),
				playPause = id == 'play-pause',
				action = playPause ? (playing ? "pause" : "play") : id;
			
			socketPlaylist(action);
			
			if (playPause){
				playing = !playing;
				
				updatePlayButton();
			}
		});
		
		$(document).on('click', '.song, .song *', function(){
			if ($(this).parents('.song-actions').length > 0)
				return;

			var song = $(this).parents('.song'), index = song.index();

			console.log(index);

			socketPlaylist('play_direct', action_data = {
				'offset': index
			});
			
			$('.song.playing').removeClass('playing');
			
			song.addClass('playing');
		});
		
		$('#song-cover').on('click', function(){
			socketPlaylist('get_state');
		});
		
		$('.progress-container').on('mousedown', function(fe){
			var progressContainer = this,
				containerStart = 0;
				total = 0,
				id = $(this).prop('id'),
				row = $(this).hasClass('row');

			if (row){
				containerStart = fe.pageX - $(progressContainer).offset().left;
				total = $(progressContainer).width();
			} else {
				containerStart = fe.pageY - $(progressContainer).offset().top;
				total = $(progressContainer).height();
			}
			
			if (containerStart < 0)
				containerStart = 0;
			else if (containerStart > total)
				containerStart = total;
			
			var percentage = containerStart / total;
			
			fe.preventDefault();

			movingProgress = true;
			seek = false;

			if (row){
				$(progressContainer).find('.progress-complete').css({
					'width': 'calc(' + (percentage * 100) + '%)'
				});
			} else {
				percentage = 1 - percentage;

				$(progressContainer).find('.progress-complete').css({
					'height': 'calc(' + (percentage * 100) + '%)'
				});
			}

			$(document).on('mousemove', function(e){
				var containerStart = 0,
					total = 0;
			
				if (row){
					containerStart = e.pageX - $(progressContainer).offset().left;
					total = $(progressContainer).width();
				} else {
					containerStart = e.pageY - $(progressContainer).offset().top;
					total = $(progressContainer).height();
				}
				
				if (containerStart < 0)
					containerStart = 0;
				else if (containerStart > total)
					containerStart = total;
				
				var percentage = containerStart / total;

				if (row){
					$(progressContainer).find('.progress-complete').css({
						'width': 'calc(' + (percentage * 100) + '%)'
					});
				} else {
					percentage = 1 - percentage;

					$(progressContainer).find('.progress-complete').css({
						'height': 'calc(' + (percentage * 100) + '%)'
					});
				}
			});
			$(document).on('mouseup', function(e){
				var containerStart = 0,
					total = 0;

				if (row){
					containerStart = e.pageX - $(progressContainer).offset().left;
					total = $(progressContainer).width();
				} else {
					containerStart = e.pageY - $(progressContainer).offset().top;
					total = $(progressContainer).height();
				}
				
				if (containerStart < 0)
					containerStart = 0;
				else if (containerStart > total)
					containerStart = total;
				
				var percentage = containerStart / total;
			
				if (!row)
					percentage = 1 - percentage;

				switch(id){
					case 'song-progress':
						var seekProgress = Math.round(roomState.song_state.track.duration_ms * percentage);
					
						socketPlaylist('seek', action_data = {
							'seek_ms': seekProgress
						});

						break;
					case 'volume-progress':
						var volume_percent = Math.round(percentage * 100);

						socketSend('user_action', {
							'action': 'set_volume',
							'action_data': {
								'volume_percent': volume_percent
							}
						});

						break;
					default:
						break;
				}

				movingProgress = false;
				
				$(document).unbind('mouseup');
				$(document).unbind('mousemove');
			});
		});
		
		$('#invite-link').on('click', function(){
			$('#invite-url').focus();
			$('#invite-url')[0].setSelectionRange(0, 99999);
			
			document.execCommand("copy");
			
			$(this).css('transform', 'scale(1.2)');
			
			var div = this;
			
			setTimeout(function(){
				$(div).css('transform', 'scale(1)');
			}, 100);
		});

		$('#chat-box').on('keyup', function(e){
			if (e.key == 'Enter' && $(this).val().length > 0){
				socketChat('send', {
					'text': $(this).val()
				});

				$(this).val('');
			}
		});

		$('#tab-label-chat').on('click', function(){
			$('#unread-count').text('0');
			$('#unread-count').css('display', 'none');
		});

		$(document).on('click', '.preview-option.kick-user, .preview-option.kick-user *', function(){
			var username = $(this).parents('.popup-container').find('input[name="username"]').val();

			socketSend('admin', {
				'action': 'kick',
				'action_data': {
					'user': username
				}
			});
		});

		$('.overlay-option').on('click', function(){
			if ($(this).hasClass('close')){
				$(this).parents('.tab-overlay').css('display', 'none');
			}
		});

		$('#delete-room').on('click', function(e){
			if ($('#dont-delete').css('display') == 'none'){
				e.preventDefault();

				$(this).parents('form').find('.sure-label').css('display', 'block');
				$(this).val('Yes, Delete');
				$('#dont-delete').css('display', 'block');
			} else {
				$(this).parents('form').submit();

				socketSend('admin', {
					'action': 'delete',
					'action_data': {
						
					}
				});
			}
		});
		$('#leave-room').on('click', function(e){
			if ($('#dont-leave').css('display') == 'none'){
				e.preventDefault();

				$(this).parents('form').find('.sure-label').css('display', 'block');
				$(this).val('Yes, Leave');
				$(this).addClass('red');
				$('#dont-leave').css('display', 'block');
			} else {
				$(this).parents('form').submit();

				socketSend('user_action', {
					'action': 'leave',
					'action_data': {
						
					}
				});
			}
		});

		$('#dont-delete').on('click', function(e){
			e.preventDefault();

			$(this).css('display', 'none');
			$(this).parents('form').find('.sure-label').css('display', 'none');

			$('#delete-room').val('Delete Room');
		});
		$('#dont-leave').on('click', function(e){
			e.preventDefault();

			$(this).css('display', 'none');
			$(this).parents('form').find('.sure-label').css('display', 'none');

			$('#leave-room').val('Leave Room');
			$('#leave-room').removeClass('red');
		});

		$('.activity-widget-wrapper.journey').on('click', function(){
			var journeyId = $(this).find('.activity-id').val();

			socketActivity('open', action_data = {
				'activity_type': 'journey',
				'id': journeyId
			});
		});

		$(document).on('click', '.device, .device *', function(){
			var deviceId = 0;

			if ($(this).hasClass('device'))
				deviceId = $(this).find('.device-id').val();
			else
				deviceId = $(this).parents('.device').find('.device-id').val();

			socketSend('user_action', {
				'action': 'select_device',
				'action_data': {
					'device_id': deviceId
				}
			});
		});

		$('#devices-refresh').on('click', function(){
			socketSend('user_action', {
				'action': 'get_devices',
				'action_data': {
					
				}
			});
		});

		$(document).on({
			mouseenter: function () {
				console.log('mouse enter');

				$(this).parents('.song').find('.song-play').css('opacity', '0');
			},
			mouseleave: function () {
				console.log('mouse leave');

				$(this).parents('.song').find('.song-play').css('opacity', '');
			}
		}, '.song-action, .song-action *');
	}

// 	#endregion
	
// 	#region Helper Functions

	function staticFile(path){
		return staticUrl + path;
	}
	function startTimer(milli, finished){
		var seconds = milli / 1000;
		
		if (timer != null){
			window.clearInterval(timer);
		}
		
		timer = window.setInterval(function(){
			var clock = secondsToClock((roomState.song_state.track.duration_ms / 1000) - seconds - 1);
			
			if (playing){
				seconds -= 1;
				milli -= 1000;
				
				updateProgress(milli);
			}
			
			if (seconds < 0){
				finished();
				
				socketPlaylist('song_end');
				
				window.clearInterval(timer);
			}
		}, 1000);
	}
	function secondsToClock(seconds){
		var hours = Math.floor(seconds / 3600), minutes = Math.floor((seconds - hours * 3600) / 60), clock = '';
		
		seconds %= 60;
		
		if (hours > 0)
			clock += hours + ':';
		
		if (hours > 0 || minutes > 0)
			clock += (minutes < 10 && hours > 0 ? '0' : '') + minutes + ':';
		
		var clock = (hours == 0 && minutes == 0 ? ':' : '') + clock + (((minutes > 0 || hours > 0) && seconds < 10) || seconds < 10 ? '0' : '') + seconds;
		
		if (clock[0] == ':'){
			clock = '0' + clock;
		}
		
		return clock;
	}
	function secondsToLength(seconds){
		var hours = Math.floor(seconds / 3600), minutes = Math.floor((seconds - hours * 3600) / 60), clock = '';
		
		seconds %= 60;
		
		if (hours > 0)
			clock += hours + 'h ';
		
		if (hours > 0 || minutes > 0)
			clock += (minutes < 10 && hours > 0 ? '0' : '') + minutes + 'm';
		
		var clock = (hours == 0 && minutes == 0 ? ':' : '') + clock + (((minutes > 0 || hours > 0) && seconds < 10) || seconds < 10 ? '0' : '');
		
		if (clock[0] == ':'){
			clock = '0' + clock;
		}
		
		return clock;
	}
	
	function fixTimes(){
		$('.song-length').each(function(){
			$(this).text(secondsToClock(Math.round(parseInt($(this).text()) / 1000)));
		});
	}
	function updatePlayButton(){
		$('#play-pause').find('img').prop('src', playing ? pausePath : playPath);
	}
	function updateProgress(milli=roomState.song_state.track.duration_ms - roomState.song_state.progress_ms){
		var clock = secondsToClock((roomState.song_state.track.duration_ms / 1000) - (milli / 1000)),
			pure_clock = clock.split('.')[0];
		
		if (seek){
			var newPercentage = (100 - milli / roomState.song_state.track.duration_ms * 100),
				diff = (($('#song-progress-container .progress-complete').width() / ($('#song-progress-container .progress-incomplete').width() + $('#song-progress-container .progress-complete').width())) * 100) - newPercentage;

			/*if (diff > 5)
				$('#progress-complete').css('transition', 'unset');*/

			$('#song-progress-container .progress-complete').css({
				'width': 'calc(' + (100 - milli / roomState.song_state.track.duration_ms * 100) + '%)'
			});
		}

		$('#song-progress-time').text(pure_clock);
		$('#song-total-time').text(secondsToClock(roomState.song_state.track.duration_ms / 1000).split('.')[0]);
	}

// 	#endregion

//	#region Socket Functions

	function socketSend(type, data){
		var dataToSend = {
			'type': type,
			'data': data
		};

		socket.send(JSON.stringify(dataToSend));
	}
	function socketPlaylist(action, action_data = {}){
		socketSend('playlist', {
			'action': action,
			'action_data': action_data
		});
	}
	function socketChat(action, action_data = {}){
		socketSend('chat', {
			'action': action,
			'action_data': action_data
		});
	}
	function socketActivity(action, action_data = {}){
		socketSend('activity', {
			'action': action,
			'action_data': action_data
		});
	}

//	#endregion
});