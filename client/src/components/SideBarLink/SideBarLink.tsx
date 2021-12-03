import { Link, useResolvedPath, useMatch } from 'react-router-dom';

import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';

type Props = {
  to: string,
  text: string,
  icon?: React.ReactElement
};

export default function SideBarLink({ to, text, icon }: Props) {
  const resolved = useResolvedPath(to);
  const match = useMatch({ path: resolved.pathname, end: true });

  return (
    <ListItemButton component={Link} to={to} selected={Boolean(match)}>
      {icon &&
        <ListItemIcon>
          {icon}
        </ListItemIcon>
      }
      <ListItemText primary={text} />
    </ListItemButton>
  );
}
