$(document).ready(function(){

	/////////////////////////////////////////////////////////////////////////////////////
	//                                                                                 //
	//                                    VARIABLES                                    //
	//                                                                                 //
	/////////////////////////////////////////////////////////////////////////////////////
	
	const roomUrl = 'r/' + code + '/';
	const socket = new WebSocket('ws://' + window.location.host + '/ws/' + roomUrl);
	
	var timer, fullscreen = false, seek = false, movingProgress = false;
	
	init();
	
// 	#region Main Functions
	
	function updatePlaylist(){
		const songState = roomState.song_state,
			  playlistState = roomState.playlist_state;
		
		seek = !movingProgress;

		$('#song-image img').prop('src', songState.item.album.images[0].url);
		$('#current-song-name').text(songState.item.name);
		$('#current-song-artist').text(songState.item.artists[0].name);
		
		var timeLeft = songState.item.duration_ms - songState.progress_ms;
		
		playing = songState.is_playing;
		
		startTimer(timeLeft, function(){
			
		});
				
		updatePlayButton();
		updateProgress();
		
		if (playlistState != null){
			$('#playlist-cover img').prop('src', playlistState.images[0].url);
			$('#playlist-title').text(playlistState.name);
			$('#playlist-creator').text(playlistState.owner.display_name);
			$('#playlist-song-count').text(playlistState.tracks.total);
			
			$('#playlist-songs').empty();
			
			$('.playlist-song.playing').removeClass('playing');
			
			var i;
			
			for (i = 0; i < playlistState.tracks.items.length; i++){
				var song = playlistState.tracks.items[i],
					songPlaying = song.track.name == songState.item.name;
				
				$('#playlist-songs').append(`<div class = "playlist-song ` + (songPlaying ? 'playing' : '') + `">
												<div style = "display: flex; align-items: center;">
													<img class = "song-cover" src = "` + song.track.album.images[songPlaying ? 1 : 2].url + `">
													<p class = "song-title">` + song.track.name + `</p>
												</div>
												<p class = "song-artist">` + song.track.artists[0].name + `</p>
												<p class = "song-album">` + song.track.album.name + `</p>
												<p class = "song-user">` + song.added_by.id + `</p>
												<p class = "song-length">` + secondsToClock(Math.round(song.track.duration_ms / 1000.0)) + `</p>
											</div>`);	
			}
			
			if (playlistState.collaborative)
				$('#playlist-collab').css('display', 'block');
			else
				$('#playlist-collab').css('display', 'none');
		}
	}
	function connection(data){
		var userDiv = $('#user-' + data.connection_state.user);
		
		userDiv.remove();
		
		console.log(data.connection_state.user);
		
		if (data.connection_state.connection_type == 'join'){
			$('#user-list').append(`
				<div id = "user-` + data.connection_state.user + `" class = "user">
					<div class = "user-image"></div>
					<p class = "user-name">` + data.connection_state.user + `</p>
				</div>
			`);
		}
	}
	
// 	#endregion

// 	#region Initialization
	
	function init(){
		setupSocket();
		setupControls();
		fixTimes();
		
		if (roomState != null)
			updatePlaylist();
		
		console.log(roomState);
	}
	
	function setupSocket(){
		socket.onmessage = function(e){
			const data = JSON.parse(e.data);
			
			console.log(data);
			
			switch(data.type){
				case 'playlist':
					roomState = data.response_data;

					updatePlaylist();

					break;
				default:
					break;
			}
		}
	}
	function setupControls(){
		$('.control').on('click', function(){
			var id = $(this).attr('id'),
				playPause = id == 'play-pause',
				action = playPause ? (playing ? "pause" : "play") : id;
			
			socketPlaylist(action);
			
			if (playPause){
				playing = !playing;
				
				updatePlayButton();
			}
		});
		
		$(document).on('click', '.playlist-song', function(){
			var index = $(this).index();

			socketPlaylist('play_direct', action_data = {
				'offset': index
			});
			
			$('.playlist-song.playing').removeClass('playing');
			
			$(this).addClass('playing');
		});
		
		$('#song-cover').on('click', function(){
			socketPlaylist('get_state');
		});
		
		$('#song-progress').on('mousedown', function(fe){
			var progress = this,
				x = fe.pageX - $(progress).offset().left,
				total = $(progress).width();
			
			if (x < 0)
				x = 0;
			else if (x > total)
				x = total;
			
			var percentage = x / total;
			
			fe.preventDefault();

			movingProgress = true;
			seek = false;

			$('#progress-complete').css({
				'transition': 'unset',
				'width': 'calc(' + (percentage * 100) + '%)'
			});

			$(document).on('mousemove', function(e){
				var x = e.pageX - $(progress).offset().left,
					total = $(progress).width();
			
				if (x < 0)
					x = 0;
				else if (x > total)
					x = total;
				
				var percentage = x / total;

				$('#progress-complete').css({
					'width': 'calc(' + (percentage * 100) + '%)'
				});
			});
			$(document).on('mouseup', function(e){
				var x = e.pageX - $(progress).offset().left,
					total = $(progress).width();
			
				if (x < 0)
					x = 0;
				else if (x > total)
					x = total;
				
				var percentage = x / total,
					seekProgress = Math.round(roomState.song_state.item.duration_ms * percentage);
				
				socketPlaylist('seek', action_data = {
					'seek_ms': seekProgress
				});

				movingProgress = false;
				
				$(document).unbind('mouseup');
				$(document).unbind('mousemove');

				$('#progress-complete').css('transition', 'all 1s linear');
			});
		});
		
		$('#fullscreen').on('click', function(){
			var el = document.documentElement;
			
			var enterFullscreen = el.requestFullscreen
					|| el.webkitRequestFullScreen
					|| el.mozRequestFullScreen
					|| el.msRequestFullscreen;
			
			if (fullscreen){
				if (document.exitFullscreen){
					document.exitFullscreen();
				} else if (document.webkitExitFullscreen){
					document.webkitExitFullscreen();
				} else if (document.msExitFullscreen){
					document.msExitFullscreen();
				}
			} else
				enterFullscreen.call(el);
				
			fullscreen = !fullscreen;
		});
		
		$('#page-link').on('click', function(){
			$('#page-url').val(window.location.href);
			
			$('#page-url').focus();
			$('#page-url')[0].setSelectionRange(0, 99999);
			
			document.execCommand("copy");
			
			$(this).css('transform', 'scale(1.2)');
			
			var div = this;
			
			setTimeout(function(){
				$(div).css('transform', 'scale(1)');
			}, 100);
		});

		socket.onclose = function(e){
			$('#connection-status').css('--background-color', 'var(--red)');
			$('#connection-status-label p').text('Disconnected');
		};

		socket.onopen = function(e){
			$('#connection-status').css('--background-color', 'var(--dark-green)');
			$('#connection-status-label p').text('Connected');
		};
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
			var clock = secondsToClock((roomState.song_state.item.duration_ms / 1000) - seconds - 1);
			
			if (playing){
				seconds -= 1;
				milli -= 1000;
				
				updateProgress(milli);
			}
			
			if (seconds < 0){
				finished();
				
				socketPlaylist('get_state');
				
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
	
	function fixTimes(){
		$('.song-length').each(function(){
			$(this).text(secondsToClock(Math.round(parseInt($(this).text()) / 1000)));
		});
	}
	function updatePlayButton(){
		$('#play-pause').find('img').prop('src', playing ? pausePath : playPath);
	}
	function updateProgress(milli=roomState.song_state.item.duration_ms - roomState.song_state.progress_ms){
		var clock = secondsToClock((roomState.song_state.item.duration_ms / 1000) - (milli / 1000)),
			pure_clock = clock.split('.')[0];
		
		if (seek){
			var newPercentage = (100 - milli / roomState.song_state.item.duration_ms * 100),
				diff = (($('#progress-complete').width() / ($('#progress-incomplete').width() + $('#progress-complete').width())) * 100) - newPercentage;

			//console.log(diff);

			if (diff > 5)
				$('#progress-complete').css('transition', 'unset');

			$('#progress-complete').css({
				'width': 'calc(' + (100 - milli / roomState.song_state.item.duration_ms * 100) + '%)'
			});

			setTimeout(function(){
				if (seek)
					$('#progress-complete').css('transition', 'all 1s linear');
			}, 1000);
		}

		$('#song-progress-time').text(pure_clock);
		$('#song-total-time').text(secondsToClock(roomState.song_state.item.duration_ms / 1000).split('.')[0]);
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

//	#endregion
});