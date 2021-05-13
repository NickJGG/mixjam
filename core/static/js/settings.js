$(document).ready(function(){
    $('.radio-button').on('click', function(){
        $(this).siblings().each(function(){
            $(this).removeClass('checked');
            $(this).find('input').prop('checked', false);
        });

        $(this).addClass('checked');
        $(this).find('input').prop('checked', true);

        $(this).siblings('.radio-message').text($(this).find('.message').val());
    });

    $('.radio-button.checked').each(function(){
        $(this).siblings('.radio-message').text($(this).find('.message').val());
    });
});