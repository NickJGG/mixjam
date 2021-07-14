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

    $('.upload-button, .upload-button *').on('click', function(){
        console.log('BUTTON CLICKED');

        $(this).siblings('input').click();
    })
    $('.file-upload input').on('change', function(e){
        console.log($(this)[0].files);

        var preview = $(this).parents('.file-upload').find('.upload-preview'),
            url = URL.createObjectURL($(this)[0].files[0]);

        if (preview.find('img').length > 0)
            preview.find('img').attr('src', url);
        else
            preview.append('<img src = "' + URL.createObjectURL($(this)[0].files[0]) + '">');
        
           preview.css('display', 'block');
    });
});