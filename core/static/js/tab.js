$(document).ready(function(){
	var labelToTabId = {
		'chat': 'chat',
        'users': 'users',
	};
	
	$('.tab-selector').on('click', function(){
		var label = $(this).find('p').text().trim().toLowerCase();
		
		$('.tab-selector.selected').removeClass('selected');
		$(this).addClass('selected');
		
		$('.tab.selected').removeClass('selected');
		$('#tab-' + labelToTabId[label]).addClass('selected');
	});
});