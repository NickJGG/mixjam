$(document).ready(function(){
    //	#region VARIABLES

        const ws_scheme = window.location.protocol == 'https:' ? 'wss' : 'ws';
        const roomUrl = 'r/' + code + '/';
        
        var socket, timer;
        var deviceActive, seek = false, movingProgress = false;

        var playlist, playback, currentSong;

    //	#endregion

    //	#region INITIALIZATION

        function init(){
            setupSocket();
            setupListeners();
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
                        updateConnections();

                        break;
                    case 'playback':
                        playlist.playback = data.response_data.playback;

                        updatePlayback();

                        break;
                    case 'playlist':
                        playlist = data.response_data.playlist;

                        updatePlaylist();

                        break;
                    case 'devices':
                        updateDevices(data.response_data);

                        break;
                    case 'admin':
                        updateAdmin();

                        break;
                    default:
                        break;
                }
            }
        }
        function setupListeners(){
            $(document).on('click', '.pl-song, .pl-song *', function(){
                if ($(this).parents('.song-actions').length > 0)
                    return;
    
                var song = $(this).hasClass('pl-song') ? $(this) : $(this).parents('.pl-song'), index = song.index();
    
                socketSend('playback', 'play_direct', data = {
                    'offset': index
                });
                
                $('.pl-song.playing').removeClass('playing');
                
                song.addClass('playing');
            });

            $('.song-control').on('click', function(){
                var control = $(this).hasClass('song-control') ? $(this) : $(this).parents('.song-control');

                var id = $(this).attr('id'),
                    playPause = control.hasClass('play'),
                    action = playPause ? (playlist.playback.is_playing ? 'pause' : 'play') : control.attr('class').split(' ')[2];
                
                socketSend('playback', action);
                
                if (playPause){
                    updatePlayButton();
                }
            });

            $('.refresh-devices').on('click', function(){
                socketSend('playback', 'get_devices');
            });

            $(document).on('click', '.device, .device *', function(){
                var deviceId = 0;
    
                if ($(this).hasClass('device'))
                    deviceId = $(this).find('.device-id').val();
                else
                    deviceId = $(this).parents('.device').find('.device-id').val();
    
                socketSend('playback', 'select_device', {
                    'device_id': deviceId
                });
            });

            $(document).on({
                mouseenter: function () {
                    $(this).parents('.pl-song').addClass('disabled');
                },
                mouseleave: function () {
                    $(this).parents('.pl-song').removeClass('disabled');
                }
            }, '.song-action');

            setupProgressContainers();
        }
        function setupProgressContainers(){
            $('.progress-container').on('mousedown touchstart', function(fe){
                var progressContainer = this,
                    containerStart = 0;
                    total = 0,
                    type = $(this).prop('class').split(' ')[0],
                    row = $(this).hasClass('row');
                
                $(progressContainer).addClass('tapping');
    
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
    
                $(document).on('mousemove touchmove', function(e){
                    $(progressContainer).addClass('tapping');

                    var containerStart = 0,
                        total = 0,
                        eventObj = e;
                
                    if (e.type == 'touchmove')
                        eventObj = e.originalEvent.touches[0] || e.originalEvent.changedTouches[0];

                    if (row){
                        containerStart = eventObj.pageX - $(progressContainer).offset().left;
                        total = $(progressContainer).width();
                    } else {
                        containerStart = eventObj.pageY - $(progressContainer).offset().top;
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
                $(document).on('mouseup touchend', function(e){
                    var containerStart = 0,
                        total = 0
                        eventObj = e;

                    $(progressContainer).removeClass('tapping');
    
                    if (e.type == 'touchmove')
                        eventObj = e.originalEvent.touches[0] || e.originalEvent.changedTouches[0];

                    if (row){
                        containerStart = eventObj.pageX - $(progressContainer).offset().left;
                        total = $(progressContainer).width();
                    } else {
                        containerStart = eventObj.pageY - $(progressContainer).offset().top;
                        total = $(progressContainer).height();
                    }
                    
                    if (containerStart < 0)
                        containerStart = 0;
                    else if (containerStart > total)
                        containerStart = total;
                    
                    var percentage = containerStart / total;
                
                    if (!row)
                        percentage = 1 - percentage;
    
                    switch(type){
                        case 'song-progress':
                            var seekProgress = Math.round(currentSong.track.duration_ms * percentage);
                        
                            socketSend('playback', 'seek', {
                                'seek_ms': seekProgress
                            });
    
                            break;
                        case 'volume-progress':
                            var volume_percent = Math.round(percentage * 100);
    
                            socketSend('playback', 'volume', {
                                'volume_percent': volume_percent
                            });
    
                            break;
                        default:
                            break;
                    }
    
                    movingProgress = false;
                    
                    $(document).unbind('mouseup');
                    $(document).unbind('mousemove');
                    $(document).unbind('touchend');
                    $(document).unbind('touchmove');
                });
            });
        }

        init();

    //	#endregion

    //  #region MAIN

        function updateConnections(){

        }

        function updatePlayback(){
            currentSong = playlist.tracks.items[playlist.playback.song_index];

            $('.current-song-title').text(currentSong.track.name);
            $('.current-song-artist').text(currentSong.track.artists[0].name);
            $('#song-info .current-song-image').css('background-image', 'url(' + currentSong.track.album.images[2].url) + ')';
            $('#mobile-player .current-song-image').css('background-image', 'url(' + currentSong.track.album.images[0].url) + ')';

            var timeLeft = currentSong.track.duration_ms - playlist.playback.progress_ms;
            
            startTimer(timeLeft, function(){
                
            });

            updatePlayButton();
            updateSongProgress();
        }

        function updatePlaylist(){
            updatePlayback();

            var length = 0, i;

            $('#playlist').empty();

            for (i = 0; i < playlist.tracks.items.length; i++){
				var song = playlist.tracks.items[i],
					songPlaying = i == playlist.playback.song_index;
				
				length += song.track.duration_ms;

				var songElement = $(playlist.song_block);
				songElement.find('.song-image > img').attr('src', song.track.album.images[2].url);
				songElement.find('.song-title').text(song.track.name);
				//songElement.find('.song-length').text(secondsToClock(Math.floor(song.track.duration_ms / 1000)));
				songElement.find('.song-artist').text(song.track.artists[0].name);
				songElement.find('.song-album p').text(song.track.album.name);
				songElement.find('.song-link').attr('href', song.track.external_urls.spotify);

				if (songPlaying)
					songElement.addClass('playing');

				$('#playlist').append(songElement);
			}
        }

        function updateAdmin(){

        }

        function updateDevices(data){
            var i, active = false;

            $('.device-list').empty();

            for (i = 0; i < data.devices.length; i++){
                var device = data.devices[i],
                    deviceElement = $(data.device_block);

                deviceElement.find('.device-name').text(device.name);
                deviceElement.find('.device-type').text(device.type);

                if (device.is_active){
                    deviceElement.addClass('active');

                    $('.device-container').addClass('active');

                    active = true;
                }

                $('.device-list').append(deviceElement);
            }

            if (!active)
                $('.device-container').removeClass('active');
        }

    //  #endregion

    //  #region HELPER FUNCTIONS

        function updatePlayButton(){
            if (playlist.playback.is_playing){
                $('.song-control.play img.play').hide();
                $('.song-control.play img.pause').show();
            } else {
                $('.song-control.play img.play').show();
                $('.song-control.play img.pause').hide();
            }
        }

        function startTimer(milli, finished){
            var seconds = milli / 1000;
            
            if (timer != null){
                window.clearInterval(timer);
            }
            
            timer = window.setInterval(function(){
                var clock = secondsToClock((currentSong.track.duration_ms / 1000) - seconds - 1);

                if (playlist.playback.is_playing){
                    seconds -= 1;
                    milli -= 1000;
                    
                    updateSongProgress(milli);
                }
                
                if (seconds < 0){
                    finished();
                    
                    socketSend('playback', 'song_end');
                    
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
            
            seconds = Math.floor(seconds % 60);
            
            if (hours > 0)
                clock += hours + 'h ';
            
            if (hours > 0 || minutes > 0)
                clock += (minutes < 10 && hours > 0 ? '0' : '') + minutes + 'm';
            
            var clock = (hours == 0 && minutes == 0 ? ':' : '') + clock + (((minutes > 0 || hours > 0) && seconds < 10) || seconds < 10 ? ' 0' : ' ') + seconds + 's';
    
            if (clock[0] == ':'){
                clock = '0' + clock;
            }
            
            return clock;
        }

        function updateSongProgress(milli = currentSong.track.duration_ms - playlist.playback.progress_ms){
            var clock = secondsToClock((currentSong.track.duration_ms / 1000) - (milli / 1000)),
                pure_clock = clock.split('.')[0];
            
            if (seek){
                var newPercentage = (100 - milli / currentSong.track.duration_ms * 100);
            }

            $('.song-progress-container').each(function(){
                $(this).find('.progress-complete').css({
                    'width': 'calc(' + (100 - milli / currentSong.track.duration_ms * 100) + '%)'
                });
            })
    
            $('.song-progress-time').text(pure_clock);
            $('.song-total-time').text(secondsToClock(currentSong.track.duration_ms / 1000).split('.')[0]);
        }

    //  #endregion

    //	#region SOCKET FUNCTIONS

        function socketSend(type, action, data = {}){
            var dataToSend = {
                'type': type,
                'data': Object.assign({}, {
                    'action': action,
                }, data)
            };

            socket.send(JSON.stringify(dataToSend));
        }

    //	#endregion
});