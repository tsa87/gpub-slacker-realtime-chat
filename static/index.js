
//
// Refactor helper functions
//

function setup_form(form_id, button_id) {

  const button = document.querySelector('#' + button_id)
  const form = document.querySelector('#' + form_id)

  button.disabled = true

  form.onkeyup = (key) => {
    if (form.value.length > 0) button.disabled = false
    else button.disabled = true

    if (key.keyCode==13) button.click() // Click the button if Enter is pressed
  }

  return button
}


function get_input_and_reset(form_id) {

  const form = document.querySelector('#' + form_id)

  const message = form.value
  form.value = ''

  return message
}


function append_new_message(content) {
  const board = document.querySelector('#new_messages')
  const div = document.createElement('div')

  div.className = "alert alert-info chat_messages"
  div.innerHTML = content

  console.log(content)

  board.append(div)
}


function scroll_to_bottom(div_id) {
  const div = document.querySelector("#" + div_id);
  div.scrollTop = div.scrollHeight;
}

//
// Start of setup
//

document.addEventListener('DOMContentLoaded', function() {
  var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);
  socket.on('connect', () => {


    //
    // Set up send new message field
    //
    const send_button = setup_form('message', 'send_button')

    send_button.onclick = () => {
      const message = get_input_and_reset('message')
      // TODO: Add TimeStamp here

      const selected_channel = document.querySelector('#current_channel').innerHTML
      socket.emit('add message', {'new_message': message, 'channel_name': selected_channel})

      return false // Force no page reload
    }


    //
    // Set up time tracker
    //
    const timer_text = document.querySelector("#timer")

    let counter = 0

    timer_text.innerHTML = counter

    setInterval(() => {
      counter ++
      timer_text.innerHTML = counter
    }, 1000)


    //
    // Set up add channel
    //
    const new_channel_button = setup_form('channel_name', 'new_channel_button')

    new_channel_button.onclick = () => {
      const request = new XMLHttpRequest()
      var channel_name = get_input_and_reset('channel_name')

      request.open('POST', '/new/channel')

      // what to do when the request is done
      request.onload = () => {
        const response = JSON.parse(request.responseText)

        if (response.success) alert('Channel successfully added!')
        else alert('Something went wrong')
      }

      const data = new FormData()
      data.append('channel_name', channel_name)

      request.send(data)
    }

    //
    // VOTE
    //
    document.querySelectorAll('.vote').forEach(button => {
        button.onclick = () => {
            const selection = button.dataset.vote;
            socket.emit('submit vote', {'selection': selection});
        };
    });

  })

  socket.on('announce message', data => {
      append_new_message(`${data.selection}`)
      scroll_to_bottom("chat_window")
  });

  socket.on('vote totals', data => {
      document.querySelector('#yes').innerHTML = data.yes;
      document.querySelector('#no').innerHTML = data.no;
      document.querySelector('#maybe').innerHTML = data.maybe;
  });

})
