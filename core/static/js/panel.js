$(document).ready(function(){
	var labelToPanelId = {
		'home': 'home',
		'chat': 'chat',
		'toke journey': 'journey',
		'personalization': 'personalization',
		'privacy': 'privacy'
	};
	
	$('.subpanel-label').on('click', function(){
		var label = $(this).text().trim().toLowerCase();
		
		$('.subpanel-label.selected').removeClass('selected');
		$(this).addClass('selected');
		
		$('.subpanel.selected').removeClass('selected');
		$('#subpanel-' + label).addClass('selected');
	});
	$('.panel-label').on('click', function(){
		var label = $(this).text().trim().toLowerCase();
		
		$('.panel-label.selected').removeClass('selected');
		$(this).addClass('selected');
		
		$('.panel.selected').removeClass('selected');
		$('#panel-' + labelToPanelId[label]).addClass('selected');
	});
});