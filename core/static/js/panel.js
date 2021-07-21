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
		'room': 'room',
		'playlist': 'playlist',
	};
	
	$(document).on('click', '.subpanel-label, .subpanel-label *', function(){
		var div = $(this).hasClass('subpanel-label') ? this : $(this).parents('.subpanel-label')[0];

		var label = $(div).find('p').text().trim().toLowerCase();
		
		$('.subpanel-label.selected').removeClass('selected');
		$(div).addClass('selected');
		
		$('.subpanel.selected').removeClass('selected');
		$('#subpanel-' + label).addClass('selected');
	});
	$(document).on('click', '.panel-label, .panel-label *', function(){
		var div = $(this).hasClass('panel-label') ? this : $(this).parents('.panel-label')[0];
		
		var label = $(div).find('p').text().trim().toLowerCase();

		$('.panel-label.selected').removeClass('selected');
		$(div).addClass('selected');
		
		$('.panel.selected').removeClass('selected');
		$('#panel-' + labelToPanelId[label]).addClass('selected');
	});
});