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
	
	function updatePlaylist(roomState){
		const songState = roomState.song_state,
			  playlistState = roomState.playlist_state;
		
		$('#song-image img').prop('src', songState.item.album.images[0].url);
		$('#song-title').text(songState.item.name);
		$('#song-artist').text(songState.item.artists[0].name);
		
		var timeLeft = songState.item.duration_ms - songState.progress_ms;
		
		if (roomState.type == 'get_room_state'){
			
		}
		
		startTimer(timeLeft, function(){
			
		});
		
		if (playlistState != null){
			$('#playlist-cover img').prop('src', playlistState.images[0].url);
			$('#playlist-title').text(playlistState.name);
			$('#playlist-creator').text(playlistState.owner.display_name);
			$('#playlist-song-count').text(playlistState.tracks.total);
			
			$('#playlist-songs').empty();
			
			$('.playlist-song.playing').removeClass('playing');
			
			var i;
			
			for (i = 0; i < playlistState.tracks.items.length; i++){
				var song = playlistState.tracks.items[i];
				
				$('#playlist-songs').append(`<div class = "playlist-song ` + (song.track.name == songState.item.name ? 'playing' : '') + `">
												<div style = "display: flex; align-items: center;">
													<img class = "song-cover" src = "` + song.track.album.images[2].url + `">
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
	}
	
	function setupSocket(){
		socket.onmessage = function(e){
			const data = JSON.parse(e.data);
			
			console.log(data);
			
			if (data.room_state)
				updatePlaylist(data.room_state);
			
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
				
				$(this).find('img').prop('src', playing ? pausePath : playPath);
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
	function fixTimes(){
		$('.song-length').each(function(){
			$(this).text(secondsToClock(Math.round(parseInt($(this).text()) / 1000)));
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
			if (playing)
				seconds -= 1;
			
			if (seconds > 0)
				console.log(secondsToClock(seconds));
			else {
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
		
		return (hours == 0 && minutes == 0 ? ':' : '') + clock + (((minutes > 0 || hours > 0) && seconds < 10) || seconds < 10 ? '0' : '') + seconds;
	}
});