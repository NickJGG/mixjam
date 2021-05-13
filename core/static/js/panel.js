$(document).ready(function(){
	var labelToPanelId = {
		'home': 'home',
		'toke journey': 'journey',
		'settings': 'settings',
		'personalization': 'personalization',
		'privacy': 'privacy',
		'overview': 'overview',
		'activities': 'activities',
		'create room': 'create',
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