// The main map.
var map;
// This is only one infowindow.  We will just move it around.  Callbacks will
// set the content.
var infowindow;
var markers;
var missingMarker;
var defaultMapCenter;
var missingLatLng;
function initialize() {
  //defaultCenter = new google.maps.LatLng(42.634739, -95.174137);
  defaultMapCenter = new google.maps.LatLng(42.634739, -95.173137);
  missingLatLng = new google.maps.LatLng(42.633739, -95.175087);

  // Map props can be hardcoded.  The cemetery is unlikely to get up and move away.
  var mapProp = {
    center: defaultMapCenter,
    //zoom:18,
    zoom:17,
    mapTypeId:google.maps.MapTypeId.SATELLITE
  };

  map = new google.maps.Map(document.getElementById("googleMap"), mapProp);
  infowindow = new google.maps.InfoWindow(); // content prop to be set later

  markers = new Array();

  missingMarker = new google.maps.Marker({
      position: missingLatLng,
      icon: '/static/images/markers/red.png',
      map: null
  });
  google.maps.event.addListener(missingMarker, 'click', function(evt) {
      openInfowindow(this);
  });
}

function bitPitEgg() {
  var burial = {
    id            : 0,
    sd_type       : "",
    sd            : "",
    lot           : "",
    space         : "",
    lot_owner     : "",
    year_purch    : "",
    first_name    : "The Bit Pit, ",
    last_name     : "Home of BVU Computer Science",
    sex           : "",
    birth_date    : "N/A",
    birth_place   : "",
    death_date    : "N/A",
    age           : "",
    death_place   : "",
    death_cause   : "",
    burial_date   : "",
    notes         : "",
    more_notes    : "",
    hidden_notes  : "",
    lat           : 42.641333,
    lng           : -95.211234,
    img           : ""
  };
  return burial;
}

/**
 * Clears burial markers and the missing marker.
 */
function clearMarkers() {
  for (var i = 0; i < markers.length; i++) {
    markers[i].setMap(null);
    if (missingMarker != markers[i]) {
      markers[i] = null;
    }
  }
  while (markers.length > 0) {
    markers.pop();
  }

  //placeMarker( bitPitEgg() );
}

/**
 * Creates burial markers for any results with valid lat/lng.
 * Activates missing marker for results without a lat/lgn.
 */
function updateMarkers(ary) {
  for (var i = 0; i < ary.length; i++) {
    if (ary[i].lat != 0 && ary[i].lng != 0) {
      // Place burial marker.
      marker = makeBurialMarker(ary[i]);
      markers.push(marker);
    } else {
      if (missingMarker.map != map) {
        // Activating missing marker.
        missingMarker.setMap(map);
        missingMarker.numberMissing = 0;
        markers.push(missingMarker);
      } else {
        missingMarker.numberMissing++;
      }
    }
  }
}

/**
 * san is short for 'sanitize'.  Instead of showing blanks for field values,
 * if a field lacks a value we will show its value as 'Not listed'.
 */
function san(txt) {
  if (txt == undefined || txt.trim() == "") {
    return "<em>Not listed</em>";
  } else {
    return txt;
  }
}

function openInfowindow(marker) {
  if (marker == missingMarker) {
    infowindow.setContent('There are ' + marker.numberMissing + ' additional people '
                        + 'buried in the cemetery<br/>'
                        + 'that match your criteria, but we don\'t have location<br/>'
                        + 'information for them yet.  Please bear with us while we<br/>'
                        + 'update our site.  Thank you.');
  } else {
    var content = "<h4>" + marker.first_name + " " + marker.last_name + "</h4>"
                + "<br/><img style=\"width: 200px;\" src=\"/api/headstone/"
                      + marker.id + "\" /><br/>"
                + "<strong>Born Date:</strong> " + san(marker.birth_date)
                + "<br/>"
                + "<strong>Born Place:</strong> " + san(marker.birth_place)
                + "<br/>"
                + "<strong>Death Date:</strong> " + san(marker.death_date)
                + "<br/>"
                + "<strong>Death Place:</strong> " + san(marker.death_place)
                + "<br/>"
                + "<strong>Burial Date:</strong> " + san(marker.burial_date)
                + "<br/>"
                + "<strong>Lot Owner:</strong> " + san(marker.lot_owner);
    infowindow.setContent(content);
  }
  infowindow.open(map, marker);
}

function makeBurialMarker(burial) {
  var marker = new google.maps.Marker({
      position: new google.maps.LatLng(burial.lat, burial.lng),
      icon: '/static/images/markers/green-dot.png',
      map: map
  });

  // Add info to the marker so that we can display it later in the infowindow.
  marker.id =            burial.id;
  marker.sd_type =       burial.sd_type;
  marker.sd =            burial.sd;
  marker.lot =           burial.lot;
  marker.space =         burial.space;
  marker.lot_owner =     burial.lot_owner;
  marker.year_purch =    burial.year_purch;
  marker.first_name =    burial.first_name;
  marker.last_name =     burial.last_name;
  marker.sex =           burial.sex;
  marker.birth_date =    burial.birth_date;
  marker.birth_place =   burial.birth_place;
  marker.death_date =    burial.death_date;
  marker.age =           burial.age;
  marker.death_place =   burial.death_place;
  marker.death_cause =   burial.death_cause;
  marker.burial_date =   burial.burial_date;
  marker.notes =         burial.notes;
  marker.more_notes =    burial.more_notes;
  marker.hidden_notes =  burial.hidden_notes;
  marker.lat =           burial.lat;
  marker.lng =           burial.lng;           

  google.maps.event.addListener(marker, 'click', function(evt) {
      openInfowindow(this);
  });

  return marker;
}


google.maps.event.addDomListener(window, 'load', initialize);

function handleSearchResponse(res) {
  try {
    res = eval(res);
    console.log(res);
    console.log(res.length);
    clearMarkers();
    if (res.length == 0) {
      $('#error-message').html('No results found.');
    } else {
      updateMarkers(res);
      $('#search-btn').dropdown('toggle');
      $('#error-message').html('');
    }
  } catch (e) {
    $('#error-message').html('Search temporarily unavailable.');
    console.log(e);
  }
}

$(document).ready(function() {
  $('.dropdown-menu input, .dropdown-menu label').click(function(e) {
    // Prevent clicks on the dropdown from dismissing the dropdown.
    e.stopPropagation();
  });

  $('#do-search-btn').click(function(e) {
    // Make 'searching' feedback, probably next to do-search-btn.
    // Fire jQuery Ajax req
    $.post( '/api/search',
      {
        first_name:  $('#first_name').get(0).value,
        last_name:   $('#last_name').get(0).value,
        birth_place: $('#birth_place').get(0).value,
        birth_date:  $('#birth_date').get(0).value,
        death_place: $('#death_place').get(0).value,
        death_date:  $('#death_date').get(0).value,
        lot_owner:   $('#lot_owner').get(0).value
      },
      handleSearchResponse );
    });


    $('#reset-btn').click(function(e) {
      clearMarkers();
      map.panTo(defaultMapCenter);
    });

/*
    $('.btn-group').on('show.bs.dropdown', function () {
      console.log('got .dropdown-menu show.bs.dropdown');
    });    
    $('.btn-group').on('hide.bs.dropdown', function () {
      console.log('got .dropdown-menu hide.bs.dropdown');
    });   
*/  
});


