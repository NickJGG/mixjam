$(document).ready(function(){
	$('.widget.selector').on('click', function(){
        $('.widget.selector').removeClass('selected');
        $('.widget.selector').addClass('unselected');

        $(this).removeClass('unselected');
        $(this).addClass('selected');

        $('#create-room input').css('display', 'flex');

        $('#selected-room').val($(this).find('.room-id').val());
    });
});