﻿/* http://keith-wood.name/calendars.html
   Esperanto localisation for Gregorian/Julian calendars for jQuery.
   Written by Olivier M. (olivierweb@ifrance.com). */
(function($) {
	'use strict';
	$.calendars.calendars.gregorian.prototype.regionalOptions.eo = {
		name: 'Gregorian',
		epochs: ['BCE', 'CE'],
		monthNames: ['Januaro','Februaro','Marto','Aprilo','Majo','Junio',
		'Julio','Aŭgusto','Septembro','Oktobro','Novembro','Decembro'],
		monthNamesShort: ['Jan','Feb','Mar','Apr','Maj','Jun',
		'Jul','Aŭg','Sep','Okt','Nov','Dec'],
		dayNames: ['Dimanĉo','Lundo','Mardo','Merkredo','Ĵaŭdo','Vendredo','Sabato'],
		dayNamesShort: ['Dim','Lun','Mar','Mer','Ĵaŭ','Ven','Sab'],
		dayNamesMin: ['Di','Lu','Ma','Me','Ĵa','Ve','Sa'],
		digits: null,
		dateFormat: 'dd/mm/yyyy',
		firstDay: 0,
		isRTL: false
	};
	if ($.calendars.calendars.julian) {
		$.calendars.calendars.julian.prototype.regionalOptions.eo =
			$.calendars.calendars.gregorian.prototype.regionalOptions.eo;
	}
})(jQuery);
