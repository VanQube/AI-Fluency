import ChatWindow from './components/ChatWindow/ChatWindow';

// Title-card strip, riffing on the show's signature split-color cards
// (solid color blocks, thin black dividers, bold condensed display type).
function TitleCard() {
  return (
    <div className="mb-6 w-full max-w-md overflow-hidden rounded-sm shadow-xl">
      <div className="flex h-24 w-full">
        <div className="flex-1 bg-saul-mustard" />
        <div className="w-1 bg-saul-black" />
        <div className="flex-1 bg-saul-teal" />
        <div className="w-1 bg-saul-black" />
        <div className="flex-1 bg-saul-orange" />
      </div>
      <div className="-mt-20 flex h-24 w-full items-center justify-center">
        <h1 className="font-display text-5xl tracking-wide text-saul-black drop-shadow-[2px_2px_0_rgba(241,230,208,0.6)]">
          SECURESHIP
        </h1>
      </div>
      <div className="bg-saul-black py-1.5 text-center">
        <p className="font-typewriter text-xs italic text-saul-cream">
          Better call... SecureShip! — it's all good, man.
        </p>
      </div>
    </div>
  );
}

function App() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-saul-black p-4">
      <TitleCard />
      <ChatWindow />
    </div>
  );
}

export default App;
