$(document).ready(function(){
    $('.profile-picture-icon').each(function(){
        $(this).width($(this).height());
    });

    $(document).on('click', ':not(#user-dropdown)', function(e){
        if ($(this).prop('id') == 'user-dropdown' || $(this).parents('#user-dropdown').length > 0){
            e.stopPropagation();

            return;
        }

        if ($(this).prop('id') == 'user-container' || $(this).parents('#user-container').length > 0){
            if ($('#user-dropdown').css('display') == 'flex')
                $('#user-dropdown').css('display', 'none');
            else
                $('#user-dropdown').css('display', 'flex');
            
            e.stopPropagation();
        } else
            $('#user-dropdown').css('display', 'none');
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
});