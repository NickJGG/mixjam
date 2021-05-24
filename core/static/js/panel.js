$(document).ready(function(){
	var labelToPanelId = {
		'home': 'home',
		'journey': 'journey',
		'settings': 'settings',
		'personalization': 'personalization',
		'privacy': 'privacy',
		'overview': 'overview',
		'activities': 'activities',
		'create room': 'create',
	};
	
	$(document).on('click', '.subpanel-label', function(){
		var label = $(this).text().trim().toLowerCase();
		
		$('.subpanel-label.selected').removeClass('selected');
		$(this).addClass('selected');
		
		$('.subpanel.selected').removeClass('selected');
		$('#subpanel-' + label).addClass('selected');
	});
	$(document).on('click', '.panel-label', function(){
		var label = $(this).text().trim().toLowerCase();
		
		$('.panel-label.selected').removeClass('selected');
		$(this).addClass('selected');
		
		$('.panel.selected').removeClass('selected');
		$('#panel-' + labelToPanelId[label]).addClass('selected');
	});
});