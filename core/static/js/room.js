$(document).ready(function(){

	/////////////////////////////////////////////////////////////////////////////////////
	//                                                                                 //
	//                                    VARIABLES                                    //
	//                                                                                 //
	/////////////////////////////////////////////////////////////////////////////////////
	
	const roomUrl = 'r/' + code + '/';
	const socket = new WebSocket('ws://' + window.location.host + '/ws/' + roomUrl);
	
	var timer;
	
	/////////////////////////////////////////////////////////////////////////////////////
	//                                                                                 //
	//                                  MAIN SEQUENCE                                  //
	//                                                                                 //
	/////////////////////////////////////////////////////////////////////////////////////
	
	init();
	
	/////////////////////////////////////////////////////////////////////////////////////
	//                                                                                 //
	//                                 MAIN FUNCTIONS                                  //
	//                                                                                 //
	/////////////////////////////////////////////////////////////////////////////////////
	
	function updatePlaylist(){
		const songState = roomState.song_state,
			  playlistState = roomState.playlist_state;
		
		$('#song-image img').prop('src', songState.item.album.images[0].url);
		$('#song-title').text(songState.item.name);
		$('#song-artist').text(songState.item.artists[0].name);
		
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
	
	/////////////////////////////////////////////////////////////////////////////////////
	//                                                                                 //
	//                                	INITIALIZATION                                 //
	//                                                                                 //
	/////////////////////////////////////////////////////////////////////////////////////
	
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
			
			if (data.room_state){
				roomState = data.room_state;
				
				updatePlaylist();
			}
			
			switch (data.type){
				case 'connection':
					if (data.type == 'join'){
						
					} else {
						
					}
					
					break;
				case 'music_control':
					
				
					switch (data.action){
						case 'play':
							
						
							break;
						case 'pause':
							
						
							break;
						case 'replay':
							
						
							break;
						case 'skip':
							
						
							break;
						default:
							break;
					}
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
			
			socketSend({
				'type': 'music_control',
				'data': {
					'action': action,
				},
			});
			
			if (playPause){
				playing = !playing;
				
				updatePlayButton();
			}
		});
		
		$(document).on('click', '.playlist-song', function(){
			var index = $(this).index(),
				data = {
					'action': 'play'
				};
			
			data['offset'] = index;
			
			socketSend({
				'type': 'music_control',
				'data': data,
			});
			
			$('.playlist-song.playing').removeClass('playing');
			
			$(this).addClass('playing');
		});
		
		$('#song-cover').on('click', function(){
			socketSend({
				'type': 'get_room_state'
			});
		});
	}
	
	/////////////////////////////////////////////////////////////////////////////////////
	//                                                                                 //
	//                                HELPER FUNCTIONS                                 //
	//                                                                                 //
	/////////////////////////////////////////////////////////////////////////////////////
	
	function socketSend(data){
		socket.send(JSON.stringify(data));
	}
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
			} else {
				finished();
				
				socketSend({
					'type': 'get_room_state',
				});
				
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
		
		$('#song-progress-time').text(pure_clock);
		$('#progress-complete').css('width', 'calc(' + (100 - milli / roomState.song_state.item.duration_ms * 100) + '%)');
		$('#song-total-time').text(secondsToClock(roomState.song_state.item.duration_ms / 1000).split('.')[0]);
	}
});