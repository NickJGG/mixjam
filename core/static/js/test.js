$(document).ready(function(){
    $(document).on('click', '*', function(e){
        var div = $(e.target),
            isElement = div.hasClass('dropdown-element') || div.parents('.dropdown-element').length > 0,
            isToggle = div.hasClass('dropdown-toggle') || div.parents('.dropdown-toggle').length > 0;
        
        var container = $(this).parents('.dropdown-container').first(),
            inContainer = container.length > 0;
        
        var group = container.find('.dropdown-group').val(),
            layer = parseInt(container.find('.dropdown-layer').val());

        console.log(isElement, isToggle);

        if (!isElement || isToggle){
            if (inContainer){
                container.toggleClass('open');

                $('.dropdown-container').each(function(){
                    var otherGroup = $(this).find('.dropdown-group').val(),
                        otherLayer = parseInt($(this).find('.dropdown-layer').val());
                
                    if (group == otherGroup && layer <= otherLayer){
                        var otherContainer = $(this);

                        if (otherContainer[0] != container[0]){
                            otherContainer.removeClass('open');
                        }
                    }
                });
            } else
                $('.dropdown-container').removeClass('open');

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
        }
    });
});